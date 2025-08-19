# services/scoring.py
from datetime import datetime
from sqlalchemy import func
from models import db, Submission, SongFeedback, CircleMembership, DropCred

# --- Configuration ----------------------------------------------------------
LIKE_VALUE = "like"
DISLIKE_VALUE = "dislike"

TESTING_MODE = True   # Set False in production

# Choose the scoring formula:
#   1 => likes / possible * 10
#   2 => (likes - dislikes) / possible * 10
#   3 => Bayesian smoothing: (likes + α·μ) / (possible + α) * 10
SCORING_VERSION = 4

# Bayesian smoothing hyperparameters (only used if SCORING_VERSION=3)
BAYESIAN_ALPHA = 5    # prior strength
BAYESIAN_PRIOR_MEAN = 0.6  # default prior mean if no global data

# v3 prior knobs (already present)
BAYESIAN_ALPHA = 5
BAYESIAN_PRIOR_MEAN = 0.6

# v4B participation boost
V4_BETA = 0.5  # try 0.4–0.7
# ---------------------------------------------------------------------------


def _likes_and_dislikes_for_user(user_id: int) -> tuple[int, int]:
    base = (
        db.session.query(SongFeedback)
        .join(Submission, SongFeedback.song_id == Submission.id)
        .filter(Submission.user_id == user_id)
    )
    likes = base.filter(SongFeedback.feedback == LIKE_VALUE).count()
    dislikes = base.filter(SongFeedback.feedback == DISLIKE_VALUE).count()
    return likes or 0, dislikes or 0

def _total_possible_for_user(user_id: int) -> int:
    subs = (
        db.session.query(Submission.id, Submission.circle_id)
        .filter(Submission.user_id == user_id)
        .all()
    )
    if not subs:
        return 0
    circle_ids = {cid for _, cid in subs}
    members_by_circle = dict(
        db.session.query(
            CircleMembership.circle_id,
            func.count(CircleMembership.user_id)
        )
        .filter(CircleMembership.circle_id.in_(circle_ids))
        .group_by(CircleMembership.circle_id)
        .all()
    )
    total_possible = 0
    for _, cid in subs:
        member_count = int(members_by_circle.get(cid, 0) or 0)
        possible_for_drop = member_count if TESTING_MODE else max(0, member_count - 1)
        total_possible += possible_for_drop
    return int(total_possible)

def _global_prior_mean() -> float:
    """
    Compute μ = global mean approval rate across all users.
    """
    total_likes = db.session.query(func.count()).filter(SongFeedback.feedback == LIKE_VALUE).scalar()
    total_possible = 0

    # possible = sum_over_all_submissions(members - 1 in prod, members in test)
    all_subs = db.session.query(Submission.id, Submission.circle_id).all()
    if all_subs:
        circle_ids = {cid for _, cid in all_subs}
        members_by_circle = dict(
            db.session.query(
                CircleMembership.circle_id,
                func.count(CircleMembership.user_id)
            )
            .filter(CircleMembership.circle_id.in_(circle_ids))
            .group_by(CircleMembership.circle_id)
            .all()
        )
        for _, cid in all_subs:
            member_count = int(members_by_circle.get(cid, 0) or 0)
            possible_for_drop = member_count if TESTING_MODE else max(0, member_count - 1)
            total_possible += possible_for_drop
    if total_possible == 0:
        return BAYESIAN_PRIOR_MEAN
    return total_likes / total_possible

def _apply_formula(total_likes: int, total_dislikes: int, total_possible: int,
                   total_submissions: int, score_version: int) -> tuple[float, dict]:
    if score_version == 1:
        raw = (total_likes / total_possible) * 10.0 if total_possible > 0 else 0.0
        params = {"formula": "likes / possible * 10"}

    elif score_version == 2:
        raw = ((total_likes - total_dislikes) / total_possible) * 10.0 if total_possible > 0 else 0.0
        params = {"formula": "(likes - dislikes) / possible * 10"}

    elif score_version == 3:
        mu = _global_prior_mean()
        raw = ((total_likes + BAYESIAN_ALPHA * mu) / (total_possible + BAYESIAN_ALPHA)) * 10.0 if total_possible > 0 else 0.0
        params = {"formula": "(likes + α·μ) / (possible + α) * 10", "alpha": BAYESIAN_ALPHA, "mu": round(mu, 4)}

    elif score_version == 4:
        # v4B = v3 + participation boost
        import math
        mu = _global_prior_mean()
        base = ((total_likes + BAYESIAN_ALPHA * mu) / (total_possible + BAYESIAN_ALPHA)) * 10.0 if total_possible > 0 else 0.0
        boost = V4_BETA * (0 if total_submissions <= 0 else math.log1p(total_submissions))
        raw = base + boost
        params = {
            "formula": "v3 + beta*log(1+submissions)",
            "alpha": BAYESIAN_ALPHA,
            "mu": round(mu, 4),
            "beta": V4_BETA,
            "base_v3": round(base, 3),
            "submissions": int(total_submissions),
        }

    else:
        raise ValueError(f"Unknown SCORING_VERSION: {score_version}")

    score = max(0.0, min(10.0, raw))  # clamp to [0,10]
    return round(score, 1), params

def compute_drop_cred(user_id: int, score_version: int | None = None) -> dict:
    version = score_version if score_version is not None else SCORING_VERSION
    total_likes, total_dislikes = _likes_and_dislikes_for_user(user_id)
    total_possible = _total_possible_for_user(user_id)
    total_submissions = db.session.query(func.count(Submission.id))\
                                  .filter(Submission.user_id == user_id)\
                                  .scalar() or 0
    drop_cred_score, params = _apply_formula(
        total_likes, total_dislikes, total_possible, total_submissions, version
    )
    params["total_submissions"] = int(total_submissions)
    params["possible_method"] = "members_including_self" if TESTING_MODE else "members_minus_self"
    params["version"] = version
    return {
        "user_id": user_id,
        "total_likes": total_likes,
        "total_dislikes": total_dislikes,
        "total_possible": total_possible,
        "drop_cred_score": drop_cred_score,
        "computed_at": datetime.utcnow(),
        "score_version": version,
        "params": params,
        "window_label": "lifetime",
        "window_start": None,
        "window_end": None,
    }

def recompute_and_store_drop_cred(user_id: int, score_version: int | None = None, commit: bool = True) -> DropCred:
    data = compute_drop_cred(user_id, score_version=score_version)
    row = DropCred(
        user_id=data["user_id"],
        total_likes=data["total_likes"],
        total_dislikes=data["total_dislikes"],
        total_possible=data["total_possible"],
        drop_cred_score=data["drop_cred_score"],
        computed_at=data["computed_at"],
        score_version=data["score_version"],
        params=data["params"],
        window_label=data["window_label"],
        window_start=data["window_start"],
        window_end=data["window_end"],
    )
    db.session.add(row)
    if commit:
        db.session.commit()
    return row

# helper function to snapshot all versions for a user
### Refresh drop_cred table FOR A SINGLE USER based on latest data ###
    # commit: bool = True => rows will replace and not save history
    # run for all users in jupyter notebook to refresh for all users
def snapshot_user_all_versions(user_id: int, versions=(1, 2, 3), commit: bool = True, replace: bool = False):
    if replace:
        # wipe existing rows for this user for these versions (lifetime window)
        db.session.query(DropCred)\
            .filter(DropCred.user_id == user_id,
                    DropCred.score_version.in_(versions),
                    DropCred.window_label == "lifetime")\
            .delete(synchronize_session=False)

    rows = []
    for v in versions:
        data = compute_drop_cred(user_id, score_version=v)
        row = DropCred(
            user_id=data["user_id"],
            total_likes=data["total_likes"],
            total_dislikes=data["total_dislikes"],
            total_possible=data["total_possible"],
            drop_cred_score=data["drop_cred_score"],
            computed_at=data["computed_at"],
            score_version=data["score_version"],
            params=data["params"],
            window_label=data["window_label"],
            window_start=data["window_start"],
            window_end=data["window_end"],
        )
        db.session.add(row)
        rows.append(row)
    if commit:
        db.session.commit()
    return rows