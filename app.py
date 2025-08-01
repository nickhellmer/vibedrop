from flask import Flask, redirect, request, session, render_template
from utils.spotify_auth import get_auth_url, get_token, get_user_profile
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # Used for session encryption

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
    session['user'] = user_data  # Store user in session
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=8889)