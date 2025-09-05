# routes/auth.py

from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from models import db, User
from flask_bcrypt import check_password_hash, generate_password_hash

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle new user registration.
    Inputs:
        - request.form['username']
        - request.form['password']
    Outputs:
        - On success: redirects to welcome page
        - On failure: renders register.html with error flash
    Side Effects:
        - Inserts new user row in database
        - Sets session['user_id']
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password")

        if not username or not password:
            flash("Username and password required.", "error")
            return render_template("register.html")

        existing_user = User.query.filter_by(vibedrop_username=username).first()
        if existing_user:
            flash("Username already taken.", "error")
            return render_template("register.html")

        hashed_pw = generate_password_hash(password).decode("utf-8")
        new_user = User(vibedrop_username=username, password=hashed_pw)

        try:
            db.session.add(new_user)
            db.session.commit()
            session["user_id"] = new_user.id
            return redirect("/welcome")
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "error")
            return render_template("register.html")

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Authenticate existing users.
    Inputs:
        - request.form['username']
        - request.form['password']
    Outputs:
        - On success: redirect to dashboard
        - On failure: re-render login with flash
    Side Effects:
        - Sets session['user_id'] if authenticated
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password")

        user = User.query.filter_by(vibedrop_username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect("/dashboard")

        flash("Invalid username or password.", "error")
        return render_template("login.html")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """
    Log out the current user by clearing session.
    Inputs: None
    Outputs: Redirects to login page
    Side Effects: Clears session data
    """
    session.clear()
    return redirect("/login")