from flask import Flask, redirect, request, render_template, session, url_for
from models import db, User
from utils.spotify_auth import get_auth_url, get_token, get_user_profile
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vibedrop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallbackkey")
db.init_app(app)

@app.route('/')
def home():
    if 'user' in session:
        user = session['user']
        return f"🎵 Logged in as {user['display_name']} (Spotify ID: {user['id']})"
    return render_template('home.html', auth_url=get_auth_url())

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_data = get_token(code)
    access_token = token_data.get('access_token')

    if not access_token:
        return "❌ Error getting Spotify access token.", 400

    user_data = get_user_profile(access_token)

    session['user'] = {
        'id': user_data['id'],
        'display_name': user_data.get('display_name', 'Unknown'),
        'access_token': access_token
    }

    # Check if user already exists in DB
    existing = User.query.filter_by(spotify_id=user_data['id']).first()
    if existing:
        return redirect('/')
    else:
        return redirect('/register')
    
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

        return redirect('/')
    
    return render_template('register.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)