from flask import Flask, redirect, request, render_template, session, url_for, flash, current_app, jsonify
from models import db, User, SoundCircle, CircleMembership, Submission, SongFeedback, VibeScore, DropCred, Feedback
from services.scoring import compute_drop_cred, snapshot_user_all_versions, SCORING_VERSION
import spotipy
from utils.spotify_auth import get_auth_url, get_token, get_user_profile, refresh_token_if_needed
from datetime import datetime, date, time, timedelta
from dotenv import load_dotenv
import random
import string
from flask_migrate import Migrate
import os
import pytz
from functools import wraps
from sqlalchemy import func, case
from sqlalchemy import and_
from sqlalchemy import or_
from utils.sms import send_email # sms reminders 
import click # flask CLI route for user drop cred snapshot 
# from spotipy import Spotify
# import secrets  # for join codes
# from flask_sqlalchemy import SQLAlchemy
# from pytz import timezone

tz_est = pytz.timezone('US/Eastern')
tz_utc = pytz.UTC
def utcnow():
    return datetime.utcnow().replace(tzinfo=pytz.utc)

TESTING_MODE = False
AUTO_PUSH_TO_PREVIOUS = False # songs added immediately go to previous cycle 
SCORING_VERSION = 4

### LOAD ENVIRONMENT VARIABLES ######################
load_dotenv()

app = Flask(__name__)
app.permanent_session_lifetime = timedelta(days=7)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///instance/vibedrop.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallbackkey")
db.init_app(app)
migrate = Migrate(app, db)

### HELPER FUNCTIONS ######################
# get a circle's next drop time, previous drop time, and second most previous droptime 
def get_cycle_window(circle: SoundCircle) -> tuple[datetime, datetime, datetime] | None:
    tz_est = pytz.timezone("US/Eastern")
    tz_utc = pytz.UTC
    
    # Always compute “now” in EST for calendar math
    now_est = datetime.utcnow().replace(tzinfo=tz_utc).astimezone(tz_est)

    # Convert drop_time from UTC → EST (preserving intended hour like 1pm)
    drop_time_est = circle.drop_time.astimezone(tz_est)
    drop_time_obj = drop_time_est.time()

    def local_drop_datetime_est(base_date):
        # build timezone-aware EST datetime at the circle’s drop time
        return tz_est.localize(datetime.combine(base_date, drop_time_obj))

    if circle.drop_frequency.lower() == "daily":
        today_drop_est = local_drop_datetime_est(now_est.date())

        if now_est < today_drop_est:
            next_drop_est = today_drop_est
        else:
            next_drop_est = today_drop_est + timedelta(days=1)

        most_recent_drop_est = next_drop_est - timedelta(days=1)
        second_most_recent_drop_est = next_drop_est - timedelta(days=2)
        
        # convert to UTC for internal use 
        next_drop_utc = next_drop_est.astimezone(tz_utc)
        most_recent_drop_utc = most_recent_drop_est.astimezone(tz_utc)
        second_most_recent_utc = second_most_recent_drop_est.astimezone(tz_utc)

        # return UTC for internal logic
        return (
            next_drop_est.astimezone(tz_utc),
            most_recent_drop_est.astimezone(tz_utc),
            second_most_recent_drop_est.astimezone(tz_utc),
        )

    # weekly / biweekly
    if circle.drop_frequency.lower() == "weekly":
        drop_days = [circle.drop_day1]
    # elif circle.drop_frequency.lower() == "biweekly":
    #     drop_days = [circle.drop_day1, circle.drop_day2]
    else:
        return None

    # Generate drop datetimes around now (EST), then pick windows
    day_names = {"Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"}
    drop_datetimes_est = []
    for i in range(-15, 9):
        d = now_est.date() + timedelta(days=i)
        if d.strftime("%A") in drop_days:
            drop_datetimes_est.append(local_drop_datetime_est(d))

    drop_datetimes_est.sort()

    for i, dt_est in enumerate(drop_datetimes_est):
        if dt_est > now_est:
            next_drop_est = dt_est
            mr_est = drop_datetimes_est[i-1] if i-1 >= 0 else None
            smr_est = drop_datetimes_est[i-2] if i-2 >= 0 else None
            if mr_est and smr_est:
                return (
                    next_drop_est.astimezone(tz_utc),
                    mr_est.astimezone(tz_utc),
                    smr_est.astimezone(tz_utc),
                )
            return None

    # no future window found (unlikely)
    # print("[DEBUG] Unexpected: get_cycle_window() could not determine drop window.")
    return None

# replace drop cred scores directly in drop_creds table when calculated in dashboard route with "compute_drop_cred" call
def upsert_current_drop_cred(user_id: int, dc: dict) -> None:
    latest = (DropCred.query
        .filter(DropCred.user_id == user_id)
        .filter(or_(DropCred.window_label.is_(None),
                    DropCred.window_label == 'lifetime'))
        .order_by(DropCred.computed_at.desc())
        .first())

    if latest:
        latest.total_likes     = dc["total_likes"]
        latest.total_dislikes  = dc["total_dislikes"]
        latest.total_possible  = dc["total_possible"]
        latest.drop_cred_score = dc["drop_cred_score"]
        latest.computed_at     = datetime.utcnow()
        latest.score_version   = 1
        latest.params          = None
    else:
        db.session.add(DropCred(
            user_id=user_id,
            total_likes=dc["total_likes"],
            total_dislikes=dc["total_dislikes"],
            total_possible=dc["total_possible"],
            drop_cred_score=dc["drop_cred_score"],
            computed_at=datetime.utcnow(),
            score_version=1,
            window_label='lifetime',
        ))
    db.session.commit()

### ALL ROUTES ######################

@app.route("/ping")
def ping():
    return "pong"

# helps with updating database in deployed version
@app.route("/run-migrations")
def run_migrations():
    from flask_migrate import upgrade
    upgrade()
    return "✅ Migrations applied."

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html', auth_url=get_auth_url())

@app.route('/callback')
def callback():
    code = request.args.get('code')
    # print("Received code:", code) # debug line 
    token_data = get_token(code)
    # print("Token data:", token_data) # debug line
    access_token = token_data.get('access_token')
    # print("Access token:", access_token) # debug line

    if not access_token:
        return "❌ Error getting Spotify access token.", 400

    user_data = get_user_profile(access_token)
    # print("User profile response:", user_data) # debug line
    
    if user_data is None:
        return "❌ Failed to fetch Spotify profile. Please try logging in again.", 400

    # make session permanent
    session.permanent = True

    spotify_id = user_data["id"]
    display_name = user_data.get("display_name") or spotify_id
    
    # Robust expires_at (Spotify sometimes gives expires_in instead)
    expires_at = token_data.get("expires_at")
    if not isinstance(expires_at, datetime):
        expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
    
    # Get-or-create user
    user = User.query.filter_by(spotify_id=spotify_id).first()
    first_login = False
    if not user:
        first_login = True
        user = User(
            spotify_id=spotify_id,
            vibedrop_username=spotify_id,   # temporary; user will pick a nice handle on /register
            display_name=display_name,
            access_token=access_token,
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
        )
        db.session.add(user)
    else:
        user.access_token = access_token
        if token_data.get("refresh_token"):
            user.refresh_token = token_data["refresh_token"]
        user.expires_at = expires_at
    
    db.session.commit()
    
    # Store only a stable key in session
    session.clear()
    session.permanent = True
    session["user_id"] = user.id
    
    app.logger.info(f"OAuth login ok: user_id={user.id}, spotify_id={spotify_id}, first_login={first_login}")

    # Store essential user info in session (avoid using 'id' to prevent confusion)
    # Include BOTH 'spotify_id' and 'id' because other routes use both.
    session['user'] = {
        'spotify_id': spotify_id,
        'id': spotify_id,  # keep for routes that expect session['user']['id']
        'display_name': display_name,
        'access_token': access_token,
        'refresh_token': token_data.get('refresh_token'),
        'expires_at': int(expires_at.timestamp()), # or expires_at.isoformat() - previously was just expires_at
    }
    
    # First-time → username page; returning → dashboard
    return redirect(url_for('register') if first_login else url_for('dashboard'))
    # --- END REPLACE ---
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('vibedrop_username')
        spotify_id = session['user']['id']
        access_token = session['user']['access_token']

        # Check if VibeDrop username is taken
        if User.query.filter_by(vibedrop_username=username).first():
            return "❌ Username already taken. Please go back and choose another.", 400

        # # Create new user and save to DB
        # new_user = User(
        #     spotify_id=spotify_id,
        #     vibedrop_username=username,
        #     access_token=access_token
        # )
        # db.session.add(new_user)
        # db.session.commit()

        user = User.query.filter_by(spotify_id=spotify_id).first()
        if not user:
            return "❌ Session error. Please log in again.", 400
        
        user.vibedrop_username = username
        # optional: refresh access_token from session (already set in callback)
        user.access_token = access_token or user.access_token
        db.session.commit()

        return redirect(url_for('welcome'))
    
    return render_template('register.html')

# welcome page
@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

# about page
@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session or 'spotify_id' not in session['user']:
        return redirect(url_for('home'))
    
    refresh_token_if_needed(session['user'])  # Refresh token if needed

    user = User.query.filter_by(spotify_id=session['user']['spotify_id']).first()
    if not user:
        return redirect(url_for('register'))
            
    sound_circles = [membership.circle for membership in user.circle_memberships]

    # compute Drop Cred for the logged-in user
    dc = compute_drop_cred(user.id)  # assumes Flask-Login's current_user
    upsert_current_drop_cred(user.id, dc) # update drop cred score in drop_creds table for the user
    return render_template('dashboard.html',
                            user=user,
                            circles=sound_circles, 
                            drop_cred=dc["drop_cred_score"],
                            drop_cred_likes=dc["total_likes"],
                            drop_cred_dislikes=dc["total_dislikes"],
                            drop_cred_possible=dc["total_possible"],
                          )

@app.route('/create-circle', methods=['GET', 'POST'])
def create_circle():
    if request.method == 'POST':
        circle_name = request.form.get('circle_name')
        drop_frequency = request.form.get('drop_frequency')
        drop_day1 = request.form.get('drop_day1')
        drop_day2 = request.form.get('drop_day2')
        drop_time_str = request.form.get('drop_time')
        if drop_frequency.lower() == "biweekly" and drop_day1 == drop_day2:
            return "❌ For biweekly circles, please choose two different drop days.", 400

        # print("drop_time_str when selected",drop_time_str)
        
        # Convert to EST datetime (only the time matters, date is arbitrary)
        try:
            eastern = pytz.timezone("US/Eastern")
            time_obj = datetime.strptime(drop_time_str, "%I:%M %p").time()
            drop_time = eastern.localize(datetime.combine(date.today(), time_obj))
        except ValueError:
            return "❌ Invalid time format. Please use 12-hour format (e.g., 3:00 PM).", 400

        user = User.query.filter_by(spotify_id=session['user']['spotify_id']).first()

        # Generate unique invite code (simple example)
        invite_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        # print("drop_time when saved:",drop_time)
        new_circle = SoundCircle(
            circle_name=circle_name,
            drop_frequency=drop_frequency,
            drop_day1=drop_day1,
            drop_day2=drop_day2,
            drop_time=drop_time,
            invite_code=invite_code,
            creator_id=user.id
        )
        db.session.add(new_circle)
        db.session.commit()

        # Add creator as member of the circle
        membership = CircleMembership(user_id=user.id, circle_id=new_circle.id)
        db.session.add(membership)
        db.session.commit()

        return render_template(
            'circle_created.html',
            circle_name=circle_name,
            invite_code=invite_code,
            circle_id=new_circle.id
        )

    return render_template('create_circle.html')

# edit circle settings - owner only
@app.route("/circle/<int:circle_id>/edit", methods=["GET", "POST"])
def edit_circle(circle_id):
    if 'user' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(spotify_id=session['user']['spotify_id']).first()
    circle = SoundCircle.query.get_or_404(circle_id)

    if circle.creator_id is None or circle.creator_id != user.id:
        flash("Only the circle owner can edit settings.", "danger")
        return redirect(url_for("circle_dashboard", circle_id=circle_id))

    if request.method == "POST":
        circle_name = request.form.get('circle_name')
        drop_frequency = request.form.get('drop_frequency')
        drop_day1 = request.form.get('drop_day1')
        drop_day2 = request.form.get('drop_day2')
        drop_time_str = request.form.get('drop_time')

        try:
            eastern = pytz.timezone("US/Eastern")
            time_obj = datetime.strptime(drop_time_str, "%I:%M %p").time()
            drop_time = eastern.localize(datetime.combine(date.today(), time_obj))
        except ValueError:
            flash("Invalid time format. Please use 12-hour format (e.g., 3:00 PM).", "danger")
            return redirect(url_for("edit_circle", circle_id=circle.id))

        circle.circle_name = circle_name
        circle.drop_frequency = drop_frequency
        circle.drop_day1 = drop_day1
        circle.drop_day2 = drop_day2
        circle.drop_time = drop_time
        db.session.commit()

        flash("Circle updated successfully!", "success")
        return redirect(url_for("circle_dashboard", circle_id=circle.id))

    return render_template("edit_circle.html", circle=circle)

# delete circle - owner only 
@app.route("/circle/<int:circle_id>/delete", methods=["POST"])
def delete_circle(circle_id):
    if 'user' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(spotify_id=session['user']['spotify_id']).first()
    circle = SoundCircle.query.get_or_404(circle_id)

    if circle.creator_id is None or circle.creator_id != current_user.id:
        flash("Only the owner can delete this circle.", "danger")
        return redirect(url_for("circle_dashboard", circle_id=circle.id))

    db.session.delete(circle)
    db.session.commit()
    flash(f"'{circle.circle_name}' has been deleted.", "success")
    return redirect(url_for("dashboard"))

# remove member from circle - owner only 
@app.route("/circle/<int:circle_id>/remove_member/<int:user_id>", methods=["POST"])
def remove_member(circle_id, user_id):
    if 'user' not in session:
        return redirect(url_for('home'))

    current_user = User.query.filter_by(spotify_id=session['user']['spotify_id']).first()
    circle = SoundCircle.query.get_or_404(circle_id)

    if circle.creator_id != current_user.id:
        flash("Only the owner can remove members.", "danger")
        return redirect(url_for("circle_dashboard", circle_id=circle.id))

    if user_id == current_user.id:
        flash("You cannot remove yourself from your own circle.", "warning")
        return redirect(url_for("circle_dashboard", circle_id=circle.id))

    membership = CircleMembership.query.filter_by(user_id=user_id, circle_id=circle.id).first()
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash("Member removed from the circle.", "info")
    else:
        flash("Member not found in this circle.", "warning")

    return redirect(url_for("circle_dashboard", circle_id=circle.id))

@app.route('/join-circle', methods=['GET', 'POST'])
def join_circle():
    if 'user' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        code = request.form.get('circle_code')
        user = User.query.filter_by(spotify_id=session['user']['spotify_id']).first()
        circle = SoundCircle.query.filter_by(invite_code=code).first()

        if not circle:
            return "❌ Invalid invite code. Please go back and try again.", 400

        # Check if already a member
        existing = CircleMembership.query.filter_by(user_id=user.id, circle_id=circle.id).first()
        if existing:
            return f"👀 You’re already in {circle.circle_name}!"

        # Add user to circle
        membership = CircleMembership(user_id=user.id, circle_id=circle.id)
        db.session.add(membership)
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('join_circle.html')

@app.route('/circle/<int:circle_id>')
def circle_dashboard(circle_id):    
    if 'user' not in session:
        return redirect(url_for('home'))
    
    spotify_id = session['user']['spotify_id']
    user = User.query.filter_by(spotify_id=spotify_id).first()
    user_id = user.id
    
    refresh_token_if_needed(session['user'])  # Refresh token if needed

    # Get circle and members
    circle = SoundCircle.query.get_or_404(circle_id)
    members = circle.members
    # print("[DEBUG] circle drop time right before window calculation:", circle.drop_time)

    # ---------------- NEW: compute circle leader from drop_creds ----------------
    member_ids = [m.id for m in members] if members else []
    
    if member_ids:
        subq = (
            db.session.query(
                DropCred.user_id.label('uid'),
                func.max(DropCred.computed_at).label('max_at')
            )
            .filter(DropCred.user_id.in_(member_ids))
            .filter(DropCred.score_version == SCORING_VERSION)   # ← ensure v4
            # optionally keep lifetime-only:
            # .filter((DropCred.window_label.is_(None)) | (DropCred.window_label == 'lifetime'))
            .group_by(DropCred.user_id)
            .subquery()
        )
        
        latest = (
            db.session.query(User.vibedrop_username, DropCred.drop_cred_score)
            .join(DropCred, DropCred.user_id == User.id)
            .join(subq, and_(DropCred.user_id == subq.c.uid,
                             DropCred.computed_at == subq.c.max_at))
            .filter(User.id.in_(member_ids))
            .all()
        )
    # ---------------------------------------------------------------------------
    
    # Get drop window (next_drop, most_recent_drop, second_most_recent_drop)
    drop_window = get_cycle_window(circle)
    if not drop_window:
        return "Unable to determine drop cycle for this circle.", 400
    next_drop, most_recent_drop, second_most_recent_drop = drop_window
    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(pytz.timezone("US/Eastern"))
    
    # Get user_ids who have submitted since the most recent drop
    recent_submissions = Submission.query.filter(
        Submission.circle_id == circle.id,
        Submission.submitted_at >= most_recent_drop,
        Submission.submitted_at < next_drop
    ).all()
    submitted_user_ids = {sub.user_id for sub in recent_submissions}
    
    # Initialize Spotipy client
    if 'access_token' not in session['user']:
        return redirect(url_for('home'))
    sp = spotipy.Spotify(auth=session['user']['access_token'])
    
    # Categorize submissions
    all_submissions = Submission.query.filter_by(circle_id=circle.id).order_by(Submission.submitted_at.desc()).all()
    enriched_submissions = []
    previous_submissions = []
    feedback_submission_ids = [] # to save submission IDs for feedback
    
    tz_utc = pytz.UTC
    for sub in all_submissions:
        # ensure submission ts is tz-aware UTC
        ts = sub.submitted_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=tz_utc)  # assuming stored as UTC-naive
        else:
            ts = ts.astimezone(tz_utc)
        
        if ts <= second_most_recent_drop:
            continue  # Skip songs older than 2 cycles
        
        try:
            track = sp.track(sub.spotify_track_id)
            track_name = track['name']
            # print("Fetched track name:", track['name'])
            artist_name = track['artists'][0]['name']
        except Exception:
            track_name = "Unknown Vibe"
            artist_name = "Unknown Artist"

        enriched = {
            'track_name': track_name,
            'track_artist': artist_name,
            'submitted_at': ts,
            'submission_id': sub.id,
            'submitter_id': sub.user_id,
            'spotify_track_id': sub.spotify_track_id,
        }

        # print("[DEBUG] most recent drop:", most_recent_drop, "[DEBUG] next drop:", next_drop)     ### DEBUG PRINTS FOR TIMEZONES ###
        if most_recent_drop <= ts < next_drop:
            enriched_submissions.append(enriched)
        elif second_most_recent_drop <= ts < most_recent_drop:
            previous_submissions.append(enriched)
            feedback_submission_ids.append(sub.id)
        else:                                                                         ### DEBUG PRINTS FOR TIMEZONES ###
            current_app.logger.info("→ skipped (older than 2 cycles), submission_id=%s ts=%s",sub.id, ts)
    
    # ### DEBUG PRINTS FOR TIMEZONES (may need to place this within the "for sub" loop ###
    # current_app.logger.info("Summary: current=%d previous=%d",len(enriched_submissions), len(previous_submissions))
    
    # get feedback submission IDs for likes/dislikes
    feedback_entries = SongFeedback.query.filter(
        SongFeedback.user_id == user_id,
        SongFeedback.song_id.in_(feedback_submission_ids)
    ).all()

    feedback_map = {entry.song_id: entry.feedback for entry in feedback_entries}

    # boolean for if to show submissions or not 
    show_submissions = TESTING_MODE

    # After you've built previous_submissions and feedback_map
    for item in previous_submissions:
        item['user_feedback'] = feedback_map.get(item['submission_id'])

    # --- Hottest drop from last finalized cycle ---
    hottest = None
    prev_ids = [s['submission_id'] for s in previous_submissions]
    
    if prev_ids:
        likes_expr = func.sum(case((SongFeedback.feedback == 'like', 1), else_=0)).label('likes')
        dislikes_expr = func.sum(case((SongFeedback.feedback == 'dislike', 1), else_=0)).label('dislikes')
        net_expr = (func.coalesce(likes_expr, 0) - func.coalesce(dislikes_expr, 0)).label('net')

        # get top leader
        leader = (
            db.session.query(  # columns to be returned
                Submission.id.label('submission_id'),
                Submission.spotify_track_id,
                User.vibedrop_username.label('submitter_username'),
                likes_expr, dislikes_expr, net_expr,                 # uses functions created above for new caluclated columns 
            )
            .join(User, User.id == Submission.user_id)                                   # adds submitter info 
            .outerjoin(SongFeedback, SongFeedback.song_id == Submission.id)              # attaches feedback rows if any. Still includes if 0
            .filter(Submission.id.in_(prev_ids))                                         # limit results to subs from previous cycle
            .group_by(Submission.id, Submission.spotify_track_id, User.vibedrop_username)
            .order_by(net_expr.desc(),likes_expr.desc(),Submission.id.asc())
            .first()
        )

        # if tied with others, grab all others to display 
        hottest = []
        if leader:
            top_net = leader.net
            top_likes = leader.likes
        
            # 2) Fetch ALL rows that match the top net and top likes
            hottest = (
                db.session.query(
                    Submission.id.label('submission_id'),
                    Submission.spotify_track_id,
                    User.vibedrop_username.label('submitter_username'),
                    likes_expr, dislikes_expr, net_expr,
                )
                .join(User, User.id == Submission.user_id)
                .outerjoin(SongFeedback, SongFeedback.song_id == Submission.id)
                .filter(Submission.id.in_(prev_ids))
                .group_by(Submission.id, Submission.spotify_track_id, User.vibedrop_username)
                .having(net_expr == top_net)
                .having(likes_expr == top_likes)
                .order_by(Submission.id.asc())  # stable order; no longer a tiebreaker
                .all()
            )

        # Build a quick lookup from the already-enriched previous_submissions
        meta_by_id = {
            p['submission_id']: {
                'track_name': p.get('track_name') or 'Unknown Vibe',
                'track_artist': p.get('track_artist') or 'Unknown Artist',
            }
            for p in previous_submissions
        }
        
        # Convert hottest rows to dicts and attach names
        if hottest:
            enriched_hottest = []
            for row in hottest:
                info = meta_by_id.get(row.submission_id, {})
                enriched_hottest.append({
                    'submission_id': row.submission_id,
                    'spotify_track_id': row.spotify_track_id,
                    'submitter_username': row.submitter_username,
                    'likes': row.likes or 0,
                    'dislikes': row.dislikes or 0,
                    'track_name': info.get('track_name', 'Unknown Vibe'),
                    'track_artist': info.get('track_artist', 'Unknown Artist'),
                })
            hottest = enriched_hottest
    
    return render_template(
        'circle_dashboard.html',
        circle=circle,
        members=members,
        submissions=enriched_submissions if show_submissions else [],
        show_submissions=show_submissions,
        previous_submissions=previous_submissions,
        testing_mode=TESTING_MODE, 
        submitted_user_ids=submitted_user_ids,
        user_id=user_id,
        hottest=hottest, 
    )

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    # Resolve DB user from Spotify ID in session
    spotify_id = session['user'].get('spotify_id')
    user = User.query.filter_by(spotify_id=spotify_id).first_or_404()
    user_id = user.id
    
    # inputs 
    song_id = request.form.get('song_id')
    feedback_value = request.form.get('feedback')  # 'like' or 'dislike'

    # Validate inputs
    if not song_id or feedback_value not in ['like', 'dislike']:
        flash("Invalid feedback submission.")
        return redirect(request.referrer or url_for('dashboard'))

    submission = Submission.query.get(song_id)

    # Safety: don’t allow rating own submission
    if submission and submission.user_id == user_id and not TESTING_MODE:
        flash("You cannot rate your own song.")
        return redirect(request.referrer or url_for('circle_dashboard', circle_id=submission.circle_id))

    # Check if feedback already exists
    existing_feedback = SongFeedback.query.filter_by(
        user_id=user_id, song_id=song_id
    ).first()

    if existing_feedback:
        existing_feedback.feedback = feedback_value
        existing_feedback.timestamp = datetime.utcnow()
    else:
        new_feedback = SongFeedback(
            user_id=user_id,
            song_id=song_id,
            feedback=feedback_value,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_feedback)

    db.session.commit()
    flash("Feedback saved!")
    return redirect(request.referrer or url_for('circle_dashboard', circle_id=submission.circle_id))

@app.route('/circle/<int:circle_id>/submit', methods=['GET', 'POST'])
def submit_song(circle_id):
    if 'user' not in session:
        return redirect(url_for('home'))
    
    refresh_token_if_needed(session['user'])  # Refresh token if needed

    circle = SoundCircle.query.get_or_404(circle_id)
    user = User.query.filter_by(spotify_id=session['user']['spotify_id']).first()

    # Make sure user is a member of this circle
    if user not in circle.members:
        return "❌ You are not a member of this Sound Circle.", 403

    if request.method == 'POST':
        track_url = request.form.get('track_url')

        # Extract Spotify track ID from the URL
        try:
            if "track/" in track_url:
                spotify_track_id = track_url.split("track/")[1].split("?")[0]
            else:
                return "❌ Invalid Spotify track URL format.", 400
        except Exception:
            return "❌ Could not parse Spotify track URL.", 400
    
        # get drop window, next drop, and most recent drop
        drop_window = get_cycle_window(circle)
        if not drop_window:
            return "⏳ Could not determine a valid drop window for this Sound Circle.", 400
        next_drop, most_recent_drop, _ = drop_window
        
        ### DEBUG PRINTS FOR TIMEZONES ###
        app.logger.info(
            "Submit: (UTC) now=%s most_recent=%s next=%s",
            utcnow(), most_recent_drop, next_drop
        )

        # Check if this user has already submitted for today's cycle
        if not TESTING_MODE:
            existing = Submission.query.filter(
                Submission.circle_id == circle.id,
                Submission.user_id == user.id,
                Submission.submitted_at > most_recent_drop
            ).first()
            if existing:
                return "❌ You’ve already submitted a vibe for this cycle.", 400

        # Save submission
        new_submission = Submission(
            circle_id=circle.id,
            user_id=user.id,
            spotify_track_id=spotify_track_id,
            cycle_date=most_recent_drop.date(),
            submitted_at=utcnow(),
            visible_to_others=False
        )
        db.session.add(new_submission)
        db.session.commit()
        
        ### DEBUG PRINTS FOR TIMEZONES ###
        current_app.logger.info("Saved submitted_at (py): %s tz=%s", new_submission.submitted_at, new_submission.submitted_at.tzinfo)

        return redirect(url_for('circle_dashboard', circle_id=circle.id))

    return render_template('submit_song.html', circle=circle)

@app.route('/circle/<int:circle_id>/create_playlist', methods=['POST'])
def create_playlist(circle_id):
    if 'user' not in session:
        return redirect(url_for('home'))
    
    refresh_token_if_needed(session['user'])  # Refresh token if needed
    user = User.query.filter_by(spotify_id=session['user']['spotify_id']).first()
    circle = SoundCircle.query.get_or_404(circle_id)

    # Get drop window using new logic
    # print("circle drop time right before window calculation:", circle.drop_time)
    drop_window = get_cycle_window(circle)
    if not drop_window:
        return jsonify({"error": "Could not determine drop cycle."}), 400

    # save next, most recent, and second most recent drops as utc datetime for comparison in previous_submissions query
    next_drop, most_recent_drop, second_most_recent_drop = (
        drop_window[0].astimezone(pytz.utc),
        drop_window[1].astimezone(pytz.utc),
        drop_window[2].astimezone(pytz.utc),
    )

    # Get submissions from previous cycle
    previous_submissions = [
        sub for sub in Submission.query.filter_by(circle_id=circle.id).all()
        if sub.submitted_at.replace(tzinfo=pytz.utc) > second_most_recent_drop
        and sub.submitted_at.replace(tzinfo=pytz.utc) <= most_recent_drop
    ]
    
    all_subs = Submission.query.filter_by(circle_id=circle.id).all()
    # for sub in all_subs:
    #     print("submitted_at =", sub.submitted_at.isoformat())
    # print("next_drop:", next_drop)
    # print("previous_submissions", previous_submissions)
    # print("Second most recent drop:", second_most_recent_drop.isoformat())
    # print("Most recent drop:", most_recent_drop.isoformat())
    if not previous_submissions:
        return jsonify({"error": "No submissions found for the previous cycle."}), 400

    # Spotify auth
    sp = spotipy.Spotify(auth=session['user']['access_token'])

    ########## old code for trying to create a new playlist when it always made a new playlist ###########
    # # Create playlist
    # today_str = most_recent_drop.strftime('%b %d, %Y')
    # playlist_name = f"VibeDrop - {circle.circle_name} - {today_str}"
    # description = f"Vibes from the {circle.circle_name} Sound Circle on {today_str}"
    # try:
    #     playlist = sp.user_playlist_create(
    #         user=session['user']['id'],
    #         name=playlist_name,
    #         public=False,
    #         description=description
    #     )

    #     track_uris = [f"spotify:track:{sub.spotify_track_id}" for sub in previous_submissions if sub.spotify_track_id]
    #     sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)
        
    #     return jsonify({
    #         "playlist_id": playlist['id'],
    #         "playlist_uri": f"spotify://playlist/{playlist['id']}",
    #         "playlist_url": playlist['external_urls']['spotify'],
    #         "message": f"✅ Playlist '{playlist_name}' created and added to your Spotify!"
    #     })
    ########## old code for trying to create a new playlist when it always made a new playlist ###########

    # Use a stable playlist name per circle so we can re-use it
    base_name = f"VibeDrop - {circle.circle_name}"
    today_str = most_recent_drop.strftime('%b %d, %Y')
    description = f"Vibes from the {circle.circle_name} Sound Circle — updated {today_str}"

    try:
        # 1) Find existing playlist by name (paginate through playlists)
        playlist = None
        page = sp.current_user_playlists(limit=50)
        while page:
            for p in page.get("items", []):
                if p.get("name") == base_name:
                    playlist = p
                    break
            if playlist or not page.get("next"):
                break
            page = sp.next(page)

        created = False
        if not playlist:
            playlist = sp.user_playlist_create(
                user=session['user']['id'],
                name=base_name,
                public=False,
                description=description
            )
            created = True

        playlist_id = playlist["id"]

        # 2) Build track uris from previous cycle
        track_uris = [
            f"spotify:track:{sub.spotify_track_id}"
            for sub in previous_submissions
            if sub.spotify_track_id
        ]

        # 3) Optional: skip tracks already in the playlist (prevents duplicates)
        existing_ids = set()
        items_page = sp.playlist_items(
            playlist_id,
            fields="items(track(id)),next",
            limit=100
        )
        while items_page:
            for it in items_page.get("items", []):
                t = (it.get("track") or {})
                tid = t.get("id")
                if tid:
                    existing_ids.add(tid)
            if not items_page.get("next"):
                break
            items_page = sp.next(items_page)

        new_uris = [u for u in track_uris if u.split(":")[-1] not in existing_ids]

        # Spotify add-items limit is 100 per call
        for i in range(0, len(new_uris), 100):
            sp.playlist_add_items(playlist_id=playlist_id, items=new_uris[i:i+100])

        return jsonify({
            "playlist_id": playlist_id,
            "playlist_uri": f"spotify://playlist/{playlist_id}",
            "playlist_url": playlist["external_urls"]["spotify"],
            "message": (
                f"✅ Playlist created and filled!"
                if created else
                f"✅ Added {len(new_uris)} new vibe(s) to your existing playlist!"
            )
        })

    except Exception as e:
        return jsonify({"error": "Failed to create/update playlist. Try logging out and back in."}), 500

# route to the all users page 
@app.route('/all-users', methods=['GET'])
def all_users():
    # Submissions per user
    submissions_q = (
        db.session.query(
            Submission.user_id.label('u_id'),
            func.count(Submission.id).label('submission_count')
        )
        .group_by(Submission.user_id)
        .subquery()
    )

    # Feedback given per user (likes/dislikes)
    feedback_q = (
        db.session.query(
            SongFeedback.user_id.label('u_id'),
            func.sum(case((SongFeedback.feedback == 'like', 1), else_=0)).label('likes_given'),
            func.sum(case((SongFeedback.feedback == 'dislike', 1), else_=0)).label('dislikes_given'),
        )
        .group_by(SongFeedback.user_id)
        .subquery()
    )

    # 1) max(computed_at) per user
    dc_max = (
        db.session.query(
            DropCred.user_id.label("u_id"),
            func.max(DropCred.computed_at).label("max_ts"),
        )
        .group_by(DropCred.user_id)
        .subquery()
    )
    
    # 2) the actual latest DropCred row per user
    latest_dc = (
        db.session.query(
            DropCred.user_id.label("u_id"),
            DropCred.drop_cred_score.label("drop_cred"),
            DropCred.computed_at.label("computed_at"),
        )
        .join(
            dc_max,
            and_(
                DropCred.user_id == dc_max.c.u_id,
                DropCred.computed_at == dc_max.c.max_ts,
            ),
        )
        .subquery()
    )
    
    rows = (
        db.session.query(
            User.id,
            User.vibedrop_username,
            User.created_at,
            func.coalesce(submissions_q.c.submission_count, 0).label('submission_count'),
            func.coalesce(feedback_q.c.likes_given, 0).label('likes_given'),
            func.coalesce(feedback_q.c.dislikes_given, 0).label('dislikes_given'),
            func.coalesce(latest_dc.c.drop_cred, 0.0).label('drop_cred'),
        )
        .outerjoin(submissions_q, submissions_q.c.u_id == User.id)
        .outerjoin(feedback_q, feedback_q.c.u_id == User.id)
        .outerjoin(latest_dc, latest_dc.c.u_id == User.id)
        .all()
    )
    
    users_stats = [
        {
            "vibedrop_username": r.vibedrop_username,
            "created_at": r.created_at,
            "drop_cred": round(float(r.drop_cred or 0.0), 1),
            "submission_count": r.submission_count or 0,
            "likes_given": r.likes_given or 0,
            "dislikes_given": r.dislikes_given or 0,
        }
        for r in rows
    ]

    # Default sort: Drop Cred desc (tie-break by username)
    users_stats.sort(key=lambda x: (x["drop_cred"], x["vibedrop_username"].lower()), reverse=True)

    return render_template('all_users.html', users_stats=users_stats)
    
# timezone display filter helper
@app.template_filter('to_est')
def to_est_filter(dt_utc):
    if dt_utc is None:
        return ""
    # est = pytz.timezone('US/Eastern')
    # return dt_utc.astimezone(est).strftime('%b %d, %Y at %I:%M %p EST')
    dt_utc = dt_utc.astimezone(tz_utc)
    return dt_utc.astimezone(tz_est)  # <-- return datetime (not string)

@app.template_filter('datetimeformat')
def datetimeformat(value, fmt="%b %d, %Y at %I:%M %p EST"):
    if value is None:
        return ""
    return value.strftime(fmt)

@app.route('/debug/drop_window/<int:circle_id>')
def debug_drop_window(circle_id):
    circle = SoundCircle.query.get_or_404(circle_id)
    tz_eastern = pytz.timezone("US/Eastern")
    tz_utc = pytz.UTC

    now_utc = datetime.now(tz_utc)
    now_est = now_utc.astimezone(tz_eastern)

    next_drop, most_recent_drop, second_most_recent_drop = get_cycle_window(circle)

    return (
        f"Now UTC: {now_utc}\n"
        f"Now EST: {now_est}\n"
        f"Windows (as returned):\n"
        f"  next_drop:             {next_drop} (tz={getattr(next_drop, 'tzinfo', None)})\n"
        f"  most_recent_drop:      {most_recent_drop} (tz={getattr(most_recent_drop, 'tzinfo', None)})\n"
        f"  second_most_recent:    {second_most_recent_drop} (tz={getattr(second_most_recent_drop, 'tzinfo', None)})\n"
    ), 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/dev/wipe_self', methods=['GET', 'POST'])
def dev_wipe_self():
    if not app.debug:
        return "❌ Disabled outside DEBUG.", 403

    if request.method == 'GET':
        # simple form so the browser sends your session cookie on POST
        return """
        <form method="post">
          <button type="submit">Wipe my account (DEV)</button>
        </form>
        """, 200

    # POST: same deletion logic as before
    uid = session.get('user_id')
    user = db.session.get(User, uid) if uid else None
    if not user and 'user' in session:
        spid = session['user'].get('spotify_id') or session['user'].get('id')
        if spid:
            user = User.query.filter_by(spotify_id=spid).first()
    if not user:
        return "❌ No logged-in user found in session.", 400

    # --- deletion logic (same as before) ---
    user_id = user.id
    circles = SoundCircle.query.filter_by(creator_id=user_id).all()
    circle_ids = [c.id for c in circles]
    if circle_ids:
        CircleMembership.query.filter(CircleMembership.circle_id.in_(circle_ids)).delete(synchronize_session=False)
        sub_ids = [sid for (sid,) in Submission.query.with_entities(Submission.id).filter(
            Submission.circle_id.in_(circle_ids)
        ).all()]
        if sub_ids:
            SongFeedback.query.filter(SongFeedback.song_id.in_(sub_ids)).delete(synchronize_session=False)
        for c in circles:
            db.session.delete(c)

    CircleMembership.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    my_sub_ids = [sid for (sid,) in Submission.query.with_entities(Submission.id).filter_by(user_id=user_id).all()]
    if my_sub_ids:
        SongFeedback.query.filter(SongFeedback.song_id.in_(my_sub_ids)).delete(synchronize_session=False)
        Submission.query.filter(Submission.id.in_(my_sub_ids)).delete(synchronize_session=False)
    SongFeedback.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    VibeScore.query.filter((VibeScore.user1_id == user_id) | (VibeScore.user2_id == user_id)).delete(synchronize_session=False)

    db.session.delete(user)
    db.session.commit()
    session.clear()
    return "✅ Deleted your account and all related data (DEV only).", 200

# account settings (including change username functionality)
@app.route('/account-settings', methods=['GET', 'POST'])
def account_settings():
    if 'user' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(spotify_id=session['user']['spotify_id']).first()

    if request.method == 'POST':
        # Username logic
        new_username = request.form.get('new_username', '').strip()
        if new_username and new_username != user.vibedrop_username:
            if User.query.filter_by(vibedrop_username=new_username).first():
                flash('Username already taken. Please choose another one.', 'danger')
                return redirect(url_for('account_settings'))
            user.vibedrop_username = new_username
            session['user']['vibedrop_username'] = new_username
            flash('Username updated successfully!', 'success')

        # Other fields
        user.email = request.form.get('email')
        user.notifications = 'notifications' in request.form

        # ✅ NEW: SMS settings
        user.phone_number = request.form.get('phone_number')
        user.sms_notifications = 'sms_notifications' in request.form

        db.session.commit()
        flash("Settings updated!", "success")
        return redirect(url_for('account_settings'))

    return render_template('account_settings.html', user=user)

# leave circle route to be used on account settings page
@app.route('/leave_circle', methods=['POST'])
def leave_circle():
    if 'user' not in session:
        return redirect(url_for('home'))

    circle_id = request.form.get('circle_id')
    user_id = User.query.filter_by(spotify_id=session['user']['spotify_id']).first().id

    # Replace SoundCircle with your actual circle model if different
    circle = SoundCircle.query.get(circle_id)
    if not circle:
        flash('Circle not found.', 'error')
        return redirect(url_for('account_settings'))
        
    # Owners cannot leave their own circle
    if circle.creator_id is not None and circle.creator_id == user_id:
        flash('Owners cannot leave their own circle. Delete the circle instead.', 'error')
        return redirect(url_for('account_settings'))

    membership = CircleMembership.query.filter_by(user_id=user_id, circle_id=circle_id).first()
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash('You have left the circle.', 'info')

    return redirect(url_for('account_settings'))


@app.route('/send-email-reminders')
def send_email_reminders():
    now_est = utcnow().astimezone(tz_est)
    print("🔍 Running scheduled email reminder check...")
    print(f"🕒 Current EST time: {now_est.strftime('%Y-%m-%d %I:%M %p %Z')}")

    eligible_circles = SoundCircle.query.all()
    reminder_count = 0
    skipped_circles = 0

    for circle in eligible_circles:
        drop_window = get_cycle_window(circle)
        if not drop_window:
            print(f"⚠️ Circle '{circle.circle_name}' has no drop_time. Skipping.")
            skipped_circles += 1
            continue

        next_drop_utc, _, _ = drop_window
        # drop_time_est = circle.drop_time.astimezone(tz_est).replace(second=0, microsecond=0)
        next_drop_est = next_drop_utc.astimezone(tz_est).replace(second=0, microsecond=0)
        print(f"⏱ Next drop for '{circle.circle_name}': {next_drop_est.strftime('%Y-%m-%d %I:%M %p %Z')}")

        # Only process if the NEXT DROP is later *today* (EST)
        if next_drop_est.date() != now_est.date():
            print(f"❌ Skipping '{circle.circle_name}' — next drop is not today (EST).")
            skipped_circles += 1
            continue

        # Compute time until next drop
        time_diff = next_drop_est - now_est
        if time_diff.total_seconds() <= 0:
            print(f"⏳ Skipping '{circle.circle_name}' — next drop has already passed.")
            skipped_circles += 1
            continue

        hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
        minutes = remainder // 60

        if hours == 0 and minutes > 0:
            time_str = f"{minutes} minutes"
        elif hours > 0 and minutes == 0:
            time_str = f"{hours} hour{'s' if hours != 1 else ''}"
        elif hours > 0 and minutes > 0:
            time_str = f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minutes"
        else:
            time_str = "less than a minute"

        members = [u for u in circle.members if getattr(u, "email", None) and getattr(u, "sms_notifications", False)]
        if len(members) < 2:
            print(f"🚫 Skipping circle '{circle.circle_name}' — only {len(members)} eligible user(s).")
            continue

        print(f"📧 Sending reminders for '{circle.circle_name}' to {len(members)} user(s). Drop is in {time_str}.")

        for user in members:
            try:
                subject = "VibeDrop Reminder"
                message = f"🎵 Reminder from VibeDrop: {time_str} until drop time for {circle.circle_name}!"
                send_email(user.email, message)
                print(f"✅ Email sent to {user.email}")
                reminder_count += 1
            except Exception as e:
                print(f"❌ Failed to email {user.email}: {e}")

    print(f"✅ Done. {reminder_count} reminder(s) sent. {skipped_circles} circle(s) skipped.")
    return "✅ Reminder emails processed"

# route for feedback submission
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        message = request.form.get('feedback')
        
        # Correct: Get Spotify ID from session
        spotify_id = session['user']['spotify_id']

        # Lookup the internal DB user by Spotify ID
        user = User.query.filter_by(spotify_id=spotify_id).first()
        user_id = user.id if user else None  # Get internal integer ID

        new_feedback = Feedback(user_id=user_id, message=message)
        db.session.add(new_feedback)
        db.session.commit()

        flash("Thanks for the feedback!", "success")
        return redirect(url_for('feedback'))

    return render_template('feedback.html')

# TEMPORARY ROUTE (TO BE DELETED OR PROTECTED) - Run helper function in services/scoring.py to get a user drop cred snapshot
@app.route("/admin/snapshot/<int:user_id>")
def admin_snapshot(user_id):
    snapshot_user_all_versions(user_id, versions=(1,2,3,4), replace=True, commit=True)
    return f"Snapshotted user {user_id}", 200

### FOOTER LINKS IN BASE.HTML ###
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")
@app.route("/terms")
def terms():
    return render_template("terms.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5001)







