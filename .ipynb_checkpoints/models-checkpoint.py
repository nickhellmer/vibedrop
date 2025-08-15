from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import DateTime
from datetime import datetime
import pytz
# new imports 
from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import JSONB

### stable constraint naming ###
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s__%(column_0_name)s",
    "ck": "ck_%(table_name)s__%(constraint_name)s",
    "fk": "fk_%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
db = SQLAlchemy(metadata=MetaData(naming_convention=convention))

def utcnow():
    return datetime.utcnow().replace(tzinfo=pytz.utc)

# Stores all VibeDrop users (each user is one row)
class User(db.Model):
    __tablename__ = 'users'
    
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
    sms_notifications = db.Column(db.Boolean, default=False)
    phone_number = db.Column(db.String(20))
    
    # helper property to get all Sound Circles this user belongs to
    @property
    def sound_circles(self):
        return [membership.circle for membership in self.circle_memberships]
    
    def __repr__(self):
        return f"<User {self.vibedrop_username}>"

# Stores all Sound Circles (each circle is one row)
class SoundCircle(db.Model):
    __tablename__ = 'sound_circles'
    
    id = db.Column(db.Integer, primary_key=True)
    circle_name = db.Column(db.String(100), unique=True, nullable=False)
    drop_frequency = db.Column(db.String(20), nullable=False)
    drop_day1 = db.Column(db.String(20), nullable=True)
    drop_day2 = db.Column(db.String(20), nullable=True)
    drop_time = db.Column(DateTime(timezone=True), nullable=False) 
    invite_code = db.Column(db.String(10), unique=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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
    __tablename__ = 'circle_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    circle_id = db.Column(db.Integer, db.ForeignKey('sound_circles.id'), nullable=False)
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
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    circle_id = db.Column(db.Integer, db.ForeignKey('sound_circles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spotify_track_id = db.Column(db.String(100), nullable=False)
    cycle_date = db.Column(db.Date, nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    visible_to_others = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='submissions')
    
# Stores all likes/dislikes on submissions
class SongFeedback(db.Model):
    __tablename__ = 'song_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    feedback = db.Column(db.String(10), nullable=False)  # 'like' or 'dislike'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'song_id', name='unique_user_song_feedback'),)

# Stores all user–user similarity scores (Drop Index)
class VibeScore(db.Model):
    __tablename__ = 'vibe_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vibe_index = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=utcnow)

    user1 = db.relationship('User', foreign_keys=[user1_id], backref='vibe_scores_given')
    user2 = db.relationship('User', foreign_keys=[user2_id], backref='vibe_scores_received')

# stores all users' drop scores 
class DropCred(db.Model):
    __tablename__ = "drop_creds"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Raw counts used for the score at computation time
    total_likes = db.Column(db.Integer, nullable=False)
    total_dislikes = db.Column(db.Integer, nullable=False)
    total_possible = db.Column(db.Integer, nullable=False)

    # Score on the 1–10 scale (phase 1 MVP)
    drop_cred_score = db.Column(db.Float, nullable=False)

    computed_at = db.Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Versioning + parameters used to compute the score (for Phase 2/3 evolution)
    score_version = db.Column(db.SmallInteger, nullable=False, default=1)  # 1 = MVP
    params = db.Column(JSONB, nullable=True)

    # Optional explicit window if you snapshot rolling periods (kept nullable for MVP)
    window_label = db.Column(db.String(32), nullable=True)  # e.g., "lifetime", "90d", "cycle_2025wk33"
    window_start = db.Column(DateTime(timezone=True), nullable=True)
    window_end = db.Column(DateTime(timezone=True), nullable=True)

    user = db.relationship("User", backref=db.backref("drop_cred_history", lazy="dynamic"))

    __table_args__ = (
        db.Index("ix_drop_creds_user_computed_at", "user_id", "computed_at"),
    )

# feedback table
class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)