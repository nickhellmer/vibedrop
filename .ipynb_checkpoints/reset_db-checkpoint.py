from app import app, db
from models import db, User, SoundCircle, CircleMembership, Submission

with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ Database reset complete.")