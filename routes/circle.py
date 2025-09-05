# routes/circle.py

from flask import Blueprint, render_template, request, redirect, session, flash
from models import db, User, SoundCircle, CircleMembership
from sqlalchemy.exc import SQLAlchemyError

circle_bp = Blueprint("circle", __name__)


@circle_bp.route("/create_circle", methods=["GET", "POST"])
def create_circle():
    """
    Create a new Sound Circle.
    Inputs (POST):
        - form['circle_name']
        - form['join_code']
    Outputs:
        - On success: redirects to /circle_created
        - On error: re-renders create_circle.html with flash
    Side Effects:
        - Creates SoundCircle and CircleMembership rows
    """
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        circle_name = request.form.get("circle_name", "").strip()
        join_code = request.form.get("join_code", "").strip()

        if not circle_name or not join_code:
            flash("Both name and join code required.", "error")
            return render_template("create_circle.html")

        existing = SoundCircle.query.filter_by(join_code=join_code).first()
        if existing:
            flash("Join code already in use.", "error")
            return render_template("create_circle.html")

        new_circle = SoundCircle(name=circle_name, join_code=join_code)
        try:
            db.session.add(new_circle)
            db.session.flush()  # to get ID before commit

            membership = CircleMembership(
                user_id=session["user_id"],
                circle_id=new_circle.id,
                is_owner=True
            )
            db.session.add(membership)
            db.session.commit()

            return redirect("/circle_created")
        except SQLAlchemyError:
            db.session.rollback()
            flash("Circle creation failed.", "error")

    return render_template("create_circle.html")


@circle_bp.route("/circle_created")
def circle_created():
    """
    Confirmation screen after creating a circle.
    Inputs: session['user_id']
    Outputs: Renders circle_created.html
    """
    if "user_id" not in session:
        return redirect("/login")

    return render_template("circle_created.html")


@circle_bp.route("/join_circle", methods=["GET", "POST"])
def join_circle():
    """
    Join an existing Sound Circle via join code.
    Inputs (POST): form['join_code']
    Outputs:
        - Success: redirects to dashboard
        - Error: flash and re-render join_circle.html
    """
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        code = request.form.get("join_code", "").strip()
        circle = SoundCircle.query.filter_by(join_code=code).first()

        if not circle:
            flash("Circle not found.", "error")
            return render_template("join_circle.html")

        # Prevent duplicate membership
        existing = CircleMembership.query.filter_by(
            user_id=session["user_id"], circle_id=circle.id
        ).first()
        if existing:
            flash("You are already a member.", "info")
            return redirect("/dashboard")

        try:
            db.session.add(CircleMembership(
                user_id=session["user_id"],
                circle_id=circle.id,
                is_owner=False
            ))
            db.session.commit()
            flash("Joined circle successfully!", "success")
            return redirect("/dashboard")
        except SQLAlchemyError:
            db.session.rollback()
            flash("Could not join circle.", "error")

    return render_template("join_circle.html")


@circle_bp.route("/edit_circle", methods=["GET", "POST"])
def edit_circle():
    """
    Circle owner can update the circle name.
    Inputs: form['circle_name']
    Outputs: Renders edit_circle.html
    Side Effects: Updates DB if owner
    """
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    membership = CircleMembership.query.filter_by(user_id=user_id, is_owner=True).first()
    if not membership:
        flash("Only owners can edit the circle.", "error")
        return redirect("/dashboard")

    circle = membership.circle

    if request.method == "POST":
        name = request.form.get("circle_name", "").strip()
        if name:
            circle.name = name
            try:
                db.session.commit()
                flash("Circle name updated.", "success")
            except SQLAlchemyError:
                db.session.rollback()
                flash("Update failed.", "error")

    return render_template("edit_circle.html", circle=circle)


@circle_bp.route("/circle_dashboard")
def circle_dashboard():
    """
    Shows Sound Circle details for the current user.
    Inputs: session['user_id']
    Outputs: Renders circle_dashboard.html
    """
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    membership = CircleMembership.query.filter_by(user_id=user_id).first()
    if not membership:
        flash("You are not in a circle.", "error")
        return redirect("/dashboard")

    return render_template("circle_dashboard.html", circle=membership.circle, user_id=user_id)