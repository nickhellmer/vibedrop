# services/scoring.py

from sqlalchemy import func  # fine to keep
# ⛔️ Do NOT import models at module top to avoid circulars.
# from models import db, Submission, SongFeedback, CircleMembership, DropCred, User


from utils.helpers import TESTING_MODE

# --- Config ------------------------------------------------------------------
SCORING_VERSION = 4  # Current production logic


# --- Scoring Dispatcher ------------------------------------------------------
def compute_drop_cred_scores():
    """
    Entry point to recompute Drop Cred scores for all users in all circles.
    Selects version-specific function based on SCORING_VERSION.
    """
    scoring_fn = scoring_registry.get(SCORING_VERSION)
    if scoring_fn:
        scoring_fn()
    else:
        raise ValueError(f"Unsupported scoring version: {SCORING_VERSION}")


# --- Version 4: Bayesian Smoothing + Participation Bonus ---------------------
def score_v4():
    """
    Version 4 scoring: Bayesian smoothing + participation rate.
    DropCred = BayesianRating * 10 + ParticipationBonus
    """
    # ✅ Lazy imports to avoid circular import at module load
    from models import db, Submission, SongFeedback, CircleMembership, DropCred, User

    alpha = 5  # Prior strength
    mu = 0.7   # Prior mean like rate
    beta = 3   # Participation bonus multiplier

    users = User.query.all()

    for user in users:
        membership = CircleMembership.query.filter_by(user_id=user.id).first()
        if not membership:
            continue

        circle_id = membership.circle_id
        circle_members = CircleMembership.query.filter_by(circle_id=circle_id).count()

        submissions = Submission.query.filter_by(user_id=user.id, circle_id=circle_id).all()
        num_cycles = len({s.cycle_date for s in submissions})

        total_likes = 0
        total_ratings = 0

        for s in submissions:
            feedbacks = SongFeedback.query.filter_by(song_id=s.id).all()
            total_likes += sum(1 for f in feedbacks if f.feedback == "like")
            total_ratings += len(feedbacks)

        # Bayesian Smoothing (scaled to 0–10)
        smoothed = ((total_likes + alpha * mu) / (total_ratings + alpha)) * 10

        # Participation bonus: capped at 1*beta when active every week
        participation_bonus = 0 if circle_members == 1 else beta * min(num_cycles / 10, 1)

        score = round(smoothed + participation_bonus, 2)

        if TESTING_MODE:
            print(f"[SCORING v4] {user.vibedrop_username}: "
                  f"Likes={total_likes}, Rated={total_ratings}, Cycles={num_cycles}, Score={score}")

        row = DropCred.query.filter_by(user_id=user.id).first()
        if not row:
            row = DropCred(user_id=user.id, score=score)
            db.session.add(row)
        else:
            row.score = score

    db.session.commit()


# --- Scoring Version Registry ------------------------------------------------
scoring_registry = {
    4: score_v4,
    # Future versions go here
}


# --- Back-compat shims (keep app.py unchanged) -------------------------------
def compute_drop_cred(user_id: int | None = None, score_version: int | None = None) -> dict:
    """
    Historical API used by app.py.
    Current implementation recomputes scores globally using the active version.
    Returns a small dict so existing call sites that inspect a return value keep working.
    """
    compute_drop_cred_scores()
    return {"version": SCORING_VERSION, "recomputed": True}

def snapshot_user_all_versions(user_id: int) -> None:
    """
    Historical API used by app.py. If you previously snapshot per-version scores,
    wire that logic here. For now we recompute with the current version.
    """
    compute_drop_cred_scores()