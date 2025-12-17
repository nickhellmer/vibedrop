import os
import requests
import urllib.parse
from dotenv import load_dotenv
# import time
from datetime import datetime, timedelta
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import session

# Load env variables from .env
load_dotenv()

# Spotify API endpoints
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_USER_PROFILE_URL = "https://api.spotify.com/v1/me"

# Get your credentials from .env
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# What permissions we request from the user
SCOPE = "user-read-private playlist-modify-public playlist-modify-private playlist-read-private"

def get_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
    }
    return f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"

def get_token(code):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(SPOTIFY_TOKEN_URL, data=data)
    token_data = response.json()
    
    # Add expires_at (UTC timestamp for when the token expires)
    if 'expires_in' in token_data:
        token_data['expires_at'] = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
    
    return token_data

def get_user_profile(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(SPOTIFY_USER_PROFILE_URL, headers=headers)
    
    # NEW: handle failure gracefully
    if response.status_code != 200:
        print("Spotify /me request failed:")
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
        return None
    
    return response.json()

def refresh_token_if_needed(session_user):
    expires_at = session_user.get('expires_at')
    
    # Convert to UNIX timestamp if it's a datetime object
    if isinstance(expires_at, datetime):
        expires_at = int(expires_at.timestamp())

    # Skip refresh if still valid
    now = int(datetime.utcnow().timestamp())
    if now < expires_at:
        return
    print("⚠️ Token expired — refreshing...")
    
    token_info = {
        'access_token': session_user['access_token'],
        'refresh_token': session_user['refresh_token'],
        'expires_at': expires_at
    }

    sp_oauth = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope=SCOPE
    )

    refreshed = sp_oauth.refresh_access_token(token_info['refresh_token'])
    session['user']['access_token'] = refreshed['access_token']
    session['user']['expires_at'] = refreshed['expires_at']
    session.modified = True

    print("[DEBUG] Access token refreshed! New token:", refreshed['access_token'])