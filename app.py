from flask import Flask, redirect, request, render_template, session, url_for
from models import db, User, SoundCircle, CircleMembership, Submission
import spotipy
from spotipy import Spotify
from utils.spotify_auth import get_auth_url, get_token, get_user_profile, refresh_token_if_needed
from datetime import date, datetime
from dotenv import load_dotenv
import secrets  # for join codes
import random
import string
from flask_migrate import Migrate
import os
from datetime import datetime, time, timedelta
import pytz

TESTING_MODE = True

### HELPER FUNCTIONS ###
# helper function to get the current cycle's date
def get_current_cycle_date(circle: SoundCircle) -> date | None:
    now = datetime.now().astimezone(pytz.timezone("US/Eastern"))
    today_weekday = now.weekday()  # Monday=0, Sunday=6

    # Map weekday names to numbers
    day_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    
    try:
        drop_time_obj = circle.drop_time.time()
        
    except Exception:
        return None  # fail-safe

    drop_days = []
    if circle.drop_frequency.lower() == "daily":
        return now.date()

    elif circle.drop_frequency.lower() == "weekly":
        drop_days = [circle.drop_day1]

    elif circle.drop_frequency.lower() == "biweekly":
        drop_days = [circle.drop_day1, circle.drop_day2]
        
    for drop_day in drop_days:
        drop_weekday = day_map.get(drop_day)
        if drop_weekday is None:
            continue
        days_until = (drop_weekday - today_weekday) % 7
        drop_date = now.date() + timedelta(days=days_until)

        drop_datetime = pytz.timezone("US/Eastern").localize(
            datetime.combine(drop_date, drop_time_obj)
        )
        
        if now < drop_datetime:
            return drop_date  # found a valid future cycle

    return None  # past all deadlines

# helper function to get circle deadline 
def has_deadline_passed(circle):
    # Parse drop time (e.g., "3:00 PM")
    try:
        drop_time_obj = circle.drop_time.time()
    except Exception:
        return False  # fail-safe: don't show if format is invalid

    # Get today's day name (e.g., "Friday")
    today_day = datetime.now().astimezone(pytz.timezone("US/Eastern")).strftime("%A")

    # Only continue if today is one of the drop days
    if circle.drop_frequency == "daily":
        show = True
    elif circle.drop_frequency == "weekly":
        show = (today_day == circle.drop_day1)
    elif circle.drop_frequency == "biweekly":
        show = (today_day in [circle.drop_day1, circle.drop_day2])
    else:
        show = False

    if not show:
        return False

    # Build the full drop datetime in EST
    now_est = datetime.now().astimezone(pytz.timezone("US/Eastern"))
    drop_deadline = datetime.combine(now_est.date(), drop_time_obj)
    drop_deadline = pytz.timezone("US/Eastern").localize(drop_deadline)

    # Check if current time has passed the deadline
    return now_est >= drop_deadline

### END HELPER FUNCTIONS ######################



# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vibedrop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallbackkey")
db.init_app(app)
migrate = Migrate(app, db)

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

### helper to get circle's most previous set of data ###
def get_previous_cycle_date(circle: SoundCircle) -> date | None:
    now = datetime.now().astimezone(pytz.timezone("US/Eastern"))
    today = now.date()
    weekday_today = today.strftime('%A')

    if circle.drop_frequency == "daily":
        return today - timedelta(days=1)

    elif circle.drop_frequency == "weekly":
        drop_index = list(calendar.day_name).index(circle.drop_day1)
        days_back = (today.weekday() - drop_index) % 7
        if days_back == 0 and not has_deadline_passed(circle):
            days_back = 7
        return today - timedelta(days=days_back)

    elif circle.drop_frequency == "biweekly":
        drop_days = [circle.drop_day1, circle.drop_day2]
        drop_indexes = sorted(list(calendar.day_name).index(d) for d in drop_days)

        for offset in range(1, 15):
            candidate = today - timedelta(days=offset)
            if candidate.strftime('%A') in drop_days:
                return candidate

    return None

@app.route('/circle/<int:circle_id>')
def circle_dashboard(circle_id):    
    if 'user' not in session:
        return redirect(url_for('home'))
    
    refresh_token_if_needed(session['user'])  # Refresh token if needed

    # Get circle, members, and submissions
    circle = SoundCircle.query.get_or_404(circle_id)
    members = circle.members
    submissions = Submission.query.filter_by(circle_id=circle.id).order_by(Submission.submitted_at.desc()).all()

    # Initialize Spotipy client
    if 'access_token' not in session['user']:
        return redirect(url_for('home'))
    sp = spotipy.Spotify(auth=session['user']['access_token'])
    print("Access token in session:", session['user']['access_token'])

    # Enrich each submission with track name and artist
    enriched_submissions = []
    for sub in submissions:
        try:
            track = sp.track(sub.spotify_track_id)
            print("Fetched track:", track)
            track_name = track['name']
            artist_name = track['artists'][0]['name']
        except Exception:
            track_name = "Unknown Vibe"
            artist_name = "Unknown Artist"

        enriched_submissions.append({
            'track_name': track_name,
            'track_artist': artist_name,
            'submitted_at': sub.submitted_at
        })

    # boolean for if to show submissions or not 
    show_submissions = has_deadline_passed(circle) or TESTING_MODE
    
    # Previous cycle submissions
    prev_cycle_date = get_previous_cycle_date(circle)
    previous_submissions = []
    if prev_cycle_date:
        prev_subs = Submission.query.filter_by(
            circle_id=circle.id,
            cycle_date=prev_cycle_date
        ).order_by(Submission.submitted_at.desc()).all()

        for sub in prev_subs:
            try:
                track = sp.track(sub.spotify_track_id)
                track_name = track['name']
                artist_name = track['artists'][0]['name']
            except Exception:
                track_name = "Unknown Vibe"
                artist_name = "Unknown Artist"

            previous_submissions.append({
                'track_name': track_name,
                'track_artist': artist_name,
                'submitted_at': sub.submitted_at
            })

    return render_template(
        'circle_dashboard.html',
        circle=circle,
        members=members,
        submissions=enriched_submissions if show_submissions else [],
        show_submissions=show_submissions,
        previous_submissions=previous_submissions,
        testing_mode=TESTING_MODE, 
        format_time=lambda t: t.strftime("%I:%M %p EST")
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

        cycle_date = get_current_cycle_date(circle)
        if not cycle_date:
            return "⏳ You can only drop on your Sound Circle’s scheduled days.", 400

        # Check if this user has already submitted for today's cycle
        existing = Submission.query.filter_by(
            circle_id=circle.id,
            user_id=user.id,
            cycle_date=cycle_date
        ).first()
        if not TESTING_MODE:
            existing = Submission.query.filter_by(
                circle_id=circle.id,
                user_id=user.id,
                cycle_date=cycle_date
            ).first()
            if existing:
                return "❌ You’ve already submitted a vibe for this cycle.", 400

        # Save submission
        new_submission = Submission(
            circle_id=circle.id,
            user_id=user.id,
            spotify_track_id=spotify_track_id,
            cycle_date=cycle_date,
            submitted_at=datetime.now().astimezone(pytz.timezone("US/Eastern")),
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

    # Get previous cycle date
    previous_date = get_previous_cycle_date(circle)
    if not previous_date:
        return "⚠️ No previous cycle to create playlist from.", 400

    # Get submissions from previous cycle
    previous_submissions = Submission.query.filter_by(
        circle_id=circle.id,
        cycle_date=previous_date
    ).all()

    if not previous_submissions:
        return "⚠️ No submissions found for the previous cycle.", 400

    # Spotify auth
    sp = spotipy.Spotify(auth=session['user']['access_token'])

    # Create playlist
    today_str = previous_date.strftime('%b %d, %Y')
    playlist_name = f"VibeDrop - {circle.circle_name} - {today_str}"
    description = f"Vibes from the {circle.circle_name} Sound Circle on {today_str}"

    try:
        playlist = sp.user_playlist_create(
            user=session['user']['id'],
            name=playlist_name,
            public=False,
            description=description
        )

        track_uris = [f"spotify:track:{sub.spotify_track_id}" for sub in previous_submissions]
        sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)

        return f"✅ Playlist '{playlist_name}' created and added to your Spotify!", 200

    except Exception as e:
        print("Playlist creation error:", e)
        return "❌ Failed to create playlist. Try logging out and back in.", 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5001)