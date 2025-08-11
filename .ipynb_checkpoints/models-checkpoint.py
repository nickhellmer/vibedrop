from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import DateTime
from datetime import datetime
import pytz

db = SQLAlchemy()

def utcnow():
    return datetime.utcnow().replace(tzinfo=pytz.utc)

# Stores all VibeDrop users (each user is one row)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(128), unique=True, nullable=False)
    vibedrop_username = db.Column(db.String(64), unique=True, nullable=False)
    display_name = db.Column(db.String(128), nullable=True)  # Spotify display name
    email = db.Column(db.String(128), nullable=True)          # Optional
    access_token = db.Column(db.String(1024), nullable=False)
    refresh_token = db.Column(db.String(1024), nullable=True) # Needed to refresh access token when expired
    expires_at = db.Column(db.DateTime, nullable=True)
    drop_cred = db.Column(db.Float, default=5.0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    circle_memberships = db.relationship('CircleMembership', back_populates='user', cascade='all, delete-orphan')
    
    # helper property to get all Sound Circles this user belongs to
    @property
    def sound_circles(self):
        return [membership.circle for membership in self.circle_memberships]
    
    def __repr__(self):
        return f"<User {self.vibedrop_username}>"

# Stores all Sound Circles (each circle is one row)
class SoundCircle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    circle_name = db.Column(db.String(100), unique=True, nullable=False)
    drop_frequency = db.Column(db.String(20), nullable=False)
    drop_day1 = db.Column(db.String(20), nullable=True)
    drop_day2 = db.Column(db.String(20), nullable=True)
    drop_time = db.Column(DateTime, nullable=False)
    invite_code = db.Column(db.String(10), unique=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    circle_memberships = db.relationship('CircleMembership', back_populates='circle')

    # Relationships
    creator = db.relationship('User', backref='created_circles')
    submissions = db.relationship('Submission', backref='circle', cascade='all, delete-orphan')
    
    # helper property to get all members of this Sound Circle
    @property
    def members(self):
        return [membership.user for membership in self.circle_memberships]
    
    def __repr__(self):
        return f"<SoundCircle {self.circle_name}>"

# Links users to circles (one row per user–circle membership)
class CircleMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    circle_id = db.Column(db.Integer, db.ForeignKey('sound_circle.id'), nullable=False)
    joined_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship('User', back_populates='circle_memberships')
    circle = db.relationship('SoundCircle', back_populates='circle_memberships')
    
    # ensure user cannot join the same circle twice 
    __table_args__ = (
        db.UniqueConstraint('user_id', 'circle_id', name='unique_membership'),
    )
    
    def __repr__(self):
        return f"<CircleMembership user_id={self.user_id}, circle_id={self.circle_id}>"

# Stores all submitted songs, tagged by user and circle
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    circle_id = db.Column(db.Integer, db.ForeignKey('sound_circle.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    spotify_track_id = db.Column(db.String(100), nullable=False)
    cycle_date = db.Column(db.Date, nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    visible_to_others = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='submissions')
    
# Stores all likes/dislikes on submissions
class SongFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    feedback = db.Column(db.String(10), nullable=False)  # 'like' or 'dislike'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'song_id', name='unique_user_song_feedback'),)

# Stores all user–user similarity scores (Drop Index)
class VibeScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vibe_index = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=utcnow)

    user1 = db.relationship('User', foreign_keys=[user1_id], backref='vibe_scores_given')
    user2 = db.relationship('User', foreign_keys=[user2_id], backref='vibe_scores_received')