from flask import Flask, redirect, request, render_template, session, url_for, flash
from models import db, User, SoundCircle, CircleMembership, Submission
import spotipy
from spotipy import Spotify
from utils.spotify_auth import get_auth_url, get_token, get_user_profile, refresh_token_if_needed
from datetime import datetime, date, time, timedelta
from dotenv import load_dotenv
import secrets  # for join codes
import random
import string
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os
import pytz
from pytz import timezone

def utcnow():
    return datetime.utcnow().replace(tzinfo=pytz.utc)

TESTING_MODE = False
AUTO_PUSH_TO_PREVIOUS = False # songs added immediately go to previous cycle 

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
    eastern = pytz.timezone("US/Eastern")
    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(eastern)
    
    drop_time_obj = circle.drop_time.time()

    def local_drop_datetime(base_date):
        return eastern.localize(datetime.combine(base_date, drop_time_obj))

    if circle.drop_frequency.lower() == "daily":
        today_drop = local_drop_datetime(now.date()) # save today's droptime as datetime, whether today's droptime has passed or not 
        
        # save next drop 
        if now < today_drop:
            next_drop = today_drop
        else:
            next_drop = today_drop + timedelta(days=1)

        most_recent_drop = next_drop - timedelta(days=1) # save most recent drop 
        second_most_recent_drop = next_drop - timedelta(days=2) # save second most recent drop 
        return next_drop, most_recent_drop, second_most_recent_drop

    # Map weekday names to numbers
    day_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
    }

    drop_days = []
    if circle.drop_frequency.lower() == "weekly":
        drop_days = [circle.drop_day1]
    elif circle.drop_frequency.lower() == "biweekly":
        drop_days = [circle.drop_day1, circle.drop_day2]
    else:
        return None

    # Generate a list of drop datetimes for the last and next 14 days
    drop_datetimes = []
    for i in range(-15, 9):
        test_date = now.date() + timedelta(days=i)
        if test_date.strftime("%A") in drop_days:
            drop_datetimes.append(local_drop_datetime(test_date))

    # Sort and get relevant windows
    drop_datetimes = sorted(drop_datetimes)
    for i, dt in enumerate(drop_datetimes):
        if dt > now:
            next_drop = dt
            most_recent_drop = drop_datetimes[i - 1] if i - 1 >= 0 else None
            second_most_recent_drop = drop_datetimes[i - 2] if i - 2 >= 0 else None
            if most_recent_drop and second_most_recent_drop:
                return next_drop, most_recent_drop, second_most_recent_drop
            else:
                return None
    
    print("[DEBUG] Unexpected: get_cycle_window() could not determine drop window.")
    return None


# # helper function to get the current cycle's date
# def get_current_cycle_date(circle: SoundCircle) -> date | None:

# # helper function to get circle deadline 
# def has_deadline_passed(circle):

# # helper to get circle's most previous set of data #
# def get_previous_cycle_date(circle: SoundCircle) -> date | None:


### ALL ROUTES ######################

@app.route("/ping")
def ping():
    return "pong"

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html', auth_url=get_auth_url())

@app.route('/callback')
def callback():
    code = request.args.get('code')
    print("Received code:", code) # debug line 
    
    token_data = get_token(code)
    print("Token data:", token_data) # debug line
    
    access_token = token_data.get('access_token')
    print("Access token:", access_token) # debug line

    if not access_token:
        return "❌ Error getting Spotify access token.", 400

    user_data = get_user_profile(access_token)
    print("User profile response:", user_data) # debug line
    
    if user_data is None:
        return "❌ Failed to fetch Spotify profile. Please try logging in again.", 400

    # make session permanent
    session.permanent = True
    
    session['user'] = {
        'id': user_data['id'],
        'display_name': user_data.get('display_name', 'Unknown'),
        'access_token': access_token,
        'refresh_token': token_data['refresh_token'],
        'expires_at': token_data['expires_at'],
    }

    # Check if user already exists in DB
    user = User.query.filter_by(spotify_id=user_data['id']).first()
    if user:
        # Update access token info and save
        user.access_token = access_token
        user.refresh_token = token_data.get('refresh_token')
        user.expires_at = token_data.get('expires_at')
        db.session.commit()
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('register'))
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        spotify_id = session['user']['id']
        access_token = session['user']['access_token']

        # Check if VibeDrop username is taken
        if User.query.filter_by(vibedrop_username=username).first():
            return "❌ Username already taken. Please go back and choose another.", 400

        # Create new user and save to DB
        new_user = User(
            spotify_id=spotify_id,
            vibedrop_username=username,
            access_token=access_token
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    refresh_token_if_needed(session['user'])  # Refresh token if needed

    user = User.query.filter_by(spotify_id=session['user']['id']).first()
    sound_circles = [membership.circle for membership in user.circle_memberships]

    return render_template('dashboard.html',
                           username=user.vibedrop_username,
                           drop_cred=5.0,
                           circles=sound_circles)

@app.route('/create-circle', methods=['GET', 'POST'])
def create_circle():
    if request.method == 'POST':
        circle_name = request.form.get('circle_name')
        drop_frequency = request.form.get('drop_frequency')
        drop_day1 = request.form.get('drop_day1')
        drop_day2 = request.form.get('drop_day2')
        drop_time_str = request.form.get('drop_time')
        
        # Convert to EST datetime (only the time matters, date is arbitrary)
        try:
            eastern = pytz.timezone("US/Eastern")
            time_obj = datetime.strptime(drop_time_str, "%I:%M %p").time()
            drop_time = eastern.localize(datetime.combine(date.today(), time_obj))
        except ValueError:
            return "❌ Invalid time format. Please use 12-hour format (e.g., 3:00 PM).", 400

        user = User.query.filter_by(spotify_id=session['user']['id']).first()

        # Generate unique invite code (simple example)
        invite_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

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

@app.route('/join-circle', methods=['GET', 'POST'])
def join_circle():
    if 'user' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        code = request.form.get('circle_code')
        user = User.query.filter_by(spotify_id=session['user']['id']).first()
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
    
    refresh_token_if_needed(session['user'])  # Refresh token if needed

    # Get circle and members
    circle = SoundCircle.query.get_or_404(circle_id)
    members = circle.members
    
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
    print("Access token in session:", session['user']['access_token'])
    
    # Categorize submissions
    all_submissions = Submission.query.filter_by(circle_id=circle.id).order_by(Submission.submitted_at.desc()).all()
    enriched_submissions = []
    previous_submissions = []
    
    for sub in all_submissions:
        if sub.submitted_at.replace(tzinfo=pytz.utc) <= second_most_recent_drop:
            continue  # Skip songs older than 2 cycles
        
        try:
            track = sp.track(sub.spotify_track_id)
            track_name = track['name']
            print("Fetched track name:", track['name'])
            artist_name = track['artists'][0]['name']
        except Exception:
            track_name = "Unknown Vibe"
            artist_name = "Unknown Artist"

        enriched = {
            'track_name': track_name,
            'track_artist': artist_name,
            'submitted_at': sub.submitted_at
        }

        if most_recent_drop <= sub.submitted_at.replace(tzinfo=pytz.utc) < next_drop:
            enriched_submissions.append(enriched)
        elif second_most_recent_drop <= sub.submitted_at.replace(tzinfo=pytz.utc) < most_recent_drop:
            previous_submissions.append(enriched)

    # boolean for if to show submissions or not 
    show_submissions = TESTING_MODE

    return render_template(
        'circle_dashboard.html',
        circle=circle,
        members=members,
        submissions=enriched_submissions if show_submissions else [],
        show_submissions=show_submissions,
        previous_submissions=previous_submissions,
        testing_mode=TESTING_MODE, 
        submitted_user_ids=submitted_user_ids,
    )

@app.route('/circle/<int:circle_id>/submit', methods=['GET', 'POST'])
def submit_song(circle_id):
    if 'user' not in session:
        return redirect(url_for('home'))
    
    refresh_token_if_needed(session['user'])  # Refresh token if needed

    circle = SoundCircle.query.get_or_404(circle_id)
    user = User.query.filter_by(spotify_id=session['user']['id']).first()

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

        return redirect(url_for('circle_dashboard', circle_id=circle.id))

    return render_template('submit_song.html', circle=circle)

@app.route('/circle/<int:circle_id>/create_playlist', methods=['POST'])
def create_playlist(circle_id):
    if 'user' not in session:
        return redirect(url_for('home'))
    
    refresh_token_if_needed(session['user'])  # Refresh token if needed

    user = User.query.filter_by(spotify_id=session['user']['id']).first()
    circle = SoundCircle.query.get_or_404(circle_id)

    # Get drop window using new logic
    drop_window = get_cycle_window(circle)
    if not drop_window:
        return "⚠️ Could not determine drop cycle.", 400

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
    for sub in all_subs:
        print("submitted_at =", sub.submitted_at.isoformat())
    print("next_drop:", next_drop)
    print("previous_submissions", previous_submissions)
    print("Second most recent drop:", second_most_recent_drop.isoformat())
    print("Most recent drop:", most_recent_drop.isoformat())
    if not previous_submissions:
        return "⚠️ No submissions found for the previous cycle.", 400

    # Spotify auth
    sp = spotipy.Spotify(auth=session['user']['access_token'])

    # Create playlist
    today_str = most_recent_drop.strftime('%b %d, %Y')
    playlist_name = f"VibeDrop - {circle.circle_name} - {today_str}"
    description = f"Vibes from the {circle.circle_name} Sound Circle on {today_str}"

    try:
        playlist = sp.user_playlist_create(
            user=session['user']['id'],
            name=playlist_name,
            public=False,
            description=description
        )

        track_uris = [f"spotify:track:{sub.spotify_track_id}" for sub in previous_submissions if sub.spotify_track_id]
        sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)
        print("✅ Created playlist:", playlist['external_urls']['spotify'], flush=True)

        # flash(f"✅ Playlist '{playlist_name}' created on your Spotify!")
        # return redirect(url_for('circle_dashboard', circle_id=circle.id))
        return f"✅ Playlist '{playlist_name}' created and added to your Spotify!", 200

    except Exception as e:
        print("Playlist creation error:", e)
        # flash("❌ Failed to create playlist. Try logging out and back in.")
        # return redirect(url_for('circle_dashboard', circle_id=circle.id))
        return "❌ Failed to create playlist. Try logging out and back in.", 500
    
# timezone display filter helper
@app.template_filter('to_est')
def to_est_filter(dt_utc):
    if dt_utc is None:
        return ""
    est = pytz.timezone('US/Eastern')
    return dt_utc.astimezone(est).strftime('%b %d, %Y at %I:%M %p EST')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5001)