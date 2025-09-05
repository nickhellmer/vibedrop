# routes/user.py

from flask import Blueprint, render_template, request, redirect, session, flash
from models import db, User
from sqlalchemy.exc import SQLAlchemyError

user_bp = Blueprint("user", __name__)


@user_bp.route("/welcome")
def welcome():
    """
    Welcome screen shown after registration.
    Inputs: session['user_id']
    Outputs: Renders welcome.html
    """
    if "user_id" not in session:
        return redirect("/login")

    return render_template("welcome.html")


@user_bp.route("/dashboard")
def dashboard():
    """
    Main user dashboard with drop and submission info.
    Inputs: session['user_id']
    Outputs: Renders dashboard.html with user context
    """
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect("/login")

    # Template expects 'user' to be passed in
    return render_template("dashboard.html", user=user)


@user_bp.route("/account_settings", methods=["GET", "POST"])
def account_settings():
    """
    Update username, email, or SMS notifications.
    Inputs (POST):
        - form['username'] (optional)
        - form['email'] (optional)
        - form['sms'] ("on" or missing)
    Outputs:
        - On success: redirects to /account_settings with flash
        - On error: same page with flash
    """
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect("/login")

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        sms = request.form.get("sms") == "on"

        user.vibedrop_username = username or user.vibedrop_username
        user.email = email or user.email
        user.sms_notifications = sms

        try:
            db.session.commit()
            flash("Account settings updated.", "success")
            return redirect("/account_settings")
        except SQLAlchemyError:
            db.session.rollback()
            flash("Failed to update account settings.", "error")

    return render_template("account_settings.html", user=user)