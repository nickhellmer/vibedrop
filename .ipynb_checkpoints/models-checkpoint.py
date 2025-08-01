from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(128), unique=True, nullable=False)
    vibedrop_username = db.Column(db.String(64), unique=True, nullable=False)
    access_token = db.Column(db.String(512), nullable=False)