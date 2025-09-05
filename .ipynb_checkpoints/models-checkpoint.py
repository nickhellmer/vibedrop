# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialized in app.py
db = SQLAlchemy()


class User(db.Model):
    """
    Represents a registered VibeDrop user.
    Fields:
        - vibedrop_username: displayed username
        - password: hashed password
        - email: optional contact
        - sms_notifications: opt-in flag
    Relationships:
        - memberships: SoundCircle memberships
        - submissions: Songs submitted
        - feedback: Feedback left on others' songs
    """
    id = db.Column(db.Integer, primary_key=True)
    vibedrop_username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120))
    sms_notifications = db.Column(db.Boolean, default=False)

    memberships = db.relationship("CircleMembership", backref="user", cascade="all, delete")
    submissions = db.relationship("Submission", backref="user", cascade="all, delete")
    feedback = db.relationship("SongFeedback", backref="user", cascade="all, delete")


class SoundCircle(db.Model):
    """
    Represents a group of users sharing songs weekly.
    Fields:
        - name: user-facing name
        - join_code: unique text ID for joining
    Relationships:
        - members: all CircleMembership rows
        - submissions: all song drops for this circle
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    join_code = db.Column(db.String(20), nullable=False, unique=True)

    members = db.relationship("CircleMembership", backref="circle", cascade="all, delete")
    submissions = db.relationship("Submission", backref="circle", cascade="all, delete")


class CircleMembership(db.Model):
    """
    Join table between User and SoundCircle.
    Fields:
        - is_owner: whether the user created the circle
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    circle_id = db.Column(db.Integer, db.ForeignKey("sound_circle.id"), nullable=False)
    is_owner = db.Column(db.Boolean, default=False)


class Submission(db.Model):
    """
    A song submission by a user to their circle for a given cycle.
    Fields:
        - spotify_link: Spotify URL
        - cycle_date: key date for drop cycle
        - timestamp: when it was submitted
    Relationships:
        - feedback: all user feedback for this submission
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    circle_id = db.Column(db.Integer, db.ForeignKey("sound_circle.id"), nullable=False)
    spotify_link = db.Column(db.String(300), nullable=False)
    cycle_date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    feedback = db.relationship("SongFeedback", backref="submission", cascade="all, delete")


class SongFeedback(db.Model):
    """
    Represents like/dislike feedback by a user on a song.
    Fields:
        - feedback: "like" or "dislike"
    """
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submission.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    feedback = db.Column(db.String(20), nullable=False)  # "like" or "dislike"