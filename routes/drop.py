# routes/drop.py

from flask import Blueprint, render_template, request, redirect, session, flash
from models import db, User, SoundCircle, Submission, SongFeedback, CircleMembership
from utils.helpers import get_current_cycle_date
from sqlalchemy.exc import SQLAlchemyError

drop_bp = Blueprint("drop", __name__)


@drop_bp.route("/submit_song", methods=["GET", "POST"])
def submit_song():
    """
    Let users submit a Spotify link as their song drop.
    Inputs (POST):
        - form['spotify_link']
    Outputs:
        - Success: redirect to dashboard
        - Error: flash and re-render submit_song.html
    """
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    membership = CircleMembership.query.filter_by(user_id=user_id).first()
    if not membership:
        flash("Join a circle to drop songs!", "error")
        return redirect("/dashboard")

    if request.method == "POST":
        link = request.form.get("spotify_link", "").strip()
        if not link:
            flash("Please submit a link.", "error")
            return render_template("submit_song.html")

        cycle_date = get_current_cycle_date(membership.circle)

        # Prevent multiple submissions in same cycle
        existing = Submission.query.filter_by(
            user_id=user_id, circle_id=membership.circle_id, cycle_date=cycle_date
        ).first()
        if existing:
            flash("You already submitted for this drop.", "info")
            return redirect("/dashboard")

        submission = Submission(
            user_id=user_id,
            circle_id=membership.circle_id,
            spotify_link=link,
            cycle_date=cycle_date
        )
        try:
            db.session.add(submission)
            db.session.commit()
            flash("Submission received!", "success")
            return redirect("/dashboard")
        except SQLAlchemyError:
            db.session.rollback()
            flash("Failed to submit song.", "error")

    return render_template("submit_song.html")


@drop_bp.route("/feedback", methods=["GET", "POST"])
def feedback():
    """
    Collect feedback from users (like/dislike others' songs).
    Inputs (POST): song_id, action ('like' or 'dislike')
    Outputs:
        - GET: feedback page listing songs
        - POST: registers like/dislike, redirects
    """
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    membership = CircleMembership.query.filter_by(user_id=user_id).first()
    if not membership:
        flash("Join a circle to leave feedback!", "error")
        return redirect("/dashboard")

    cycle_date = get_current_cycle_date(membership.circle)

    if request.method == "POST":
        song_id = request.form.get("song_id")
        action = request.form.get("action")  # "like" or "dislike"

        if not song_id or action not in ["like", "dislike"]:
            flash("Invalid feedback.", "error")
            return redirect("/feedback")

        existing = SongFeedback.query.filter_by(
            submission_id=song_id,
            user_id=user_id
        ).first()

        if existing:
            existing.feedback = action
        else:
            feedback = SongFeedback(
                submission_id=song_id,
                user_id=user_id,
                feedback=action
            )
            db.session.add(feedback)

        try:
            db.session.commit()
            flash("Feedback saved.", "success")
        except SQLAlchemyError:
            db.session.rollback()
            flash("Failed to save feedback.", "error")

        return redirect("/feedback")

    # GET — render feedback form
    songs = Submission.query.filter(
        Submission.circle_id == membership.circle_id,
        Submission.cycle_date == cycle_date,
        Submission.user_id != user_id
    ).all()

    return render_template("feedback.html", songs=songs)