from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_session import Session
from datetime import timedelta
import os

# --- App Initialization ------------------------------------------------------

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
session = Session()

def create_app():
    """
    Flask application factory.
    Sets up app configuration, database, session, and blueprints.
    """
    app = Flask(__name__)

    # --- Configuration ---
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev")
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

    # --- Extension Setup ---
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    session.init_app(app)

    # --- Register Blueprints ---
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.circle import circle_bp
    from routes.drop import drop_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(circle_bp)
    app.register_blueprint(drop_bp)

    # --- Error Handlers (Optional TODO) ---
    # Add app-wide error handling or logging here

    return app