# services/scoring.py
from datetime import datetime
from sqlalchemy import func
from models import db, Submission, SongFeedback, CircleMembership, DropCred, User

# --- Configuration ----------------------------------------------------------
LIKE_VALUE = "like"
DISLIKE_VALUE = "dislike"

# For local solo testing you may want True (counts include self).
# In production this should be False (exclude self).
TESTING_MODE = True  # can be overridden from app.py at startup

# Choose the scoring formula shown to users by default:
#   1 => likes / possible * 10
#   2 => (likes - dislikes) / possible * 10
#   3 => Bayesian smoothing: (likes + α·μ) / (possible + α) * 10
#   4 => v3 + participation bonus: β * min(S / Smax, 1) * 10
SCORING_VERSION = 4

# v3 (Bayesian) hyperparameters
# α = prior strength (shrinkage), μ = fallback prior mean (use measured μ if available).
BAYESIAN_ALPHA = 10
BAYESIAN_PRIOR_MEAN = 0.05

# v4 participation-friendly bonus (added on top of v3)
V4_BETA = 0.05   # weight of the bonus
V4_SMAX = 10     # cap on submissions in the bonus term
# ---------------------------------------------------------------------------


def _likes_and_dislikes_for_user(user_id: int) -> tuple[int, int]:
    """
    Count likes and dislikes received on this user's submissions.
    """
    base = (
        db.session.query(SongFeedback)
        .join(Submission, SongFeedback.song_id == Submission.id)
        .filter(Submission.user_id == user_id)
    )
    likes = base.filter(SongFeedback.feedback == LIKE_VALUE).count()
    dislikes = base.filter(SongFeedback.feedback == DISLIKE_VALUE).count()
    return likes or 0, dislikes or 0


def _total_possible_for_user(user_id: int) -> int:
    """
    Denominator N = sum_over_user_submissions( members_in_circle - (exclude_self ? 1 : 0) ).
    """
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
    Compute μ = global mean approval rate across all submissions.
    μ = total_likes / total_possible, where total_possible is computed the same way
    we compute a user's denominator (sum over all submissions of circle size minus self in prod).
    Falls back to BAYESIAN_PRIOR_MEAN if no data.
    """
    total_likes = (
        db.session.query(func.count(SongFeedback.id))
        .filter(SongFeedback.feedback == LIKE_VALUE)
        .scalar()
        or 0
    )

    total_possible = 0
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

    if total_possible <= 0:
        return BAYESIAN_PRIOR_MEAN
    return float(total_likes) / float(total_possible)


def _apply_formula(
    total_likes: int,
    total_dislikes: int,
    total_possible: int,
    total_submissions: int,
    score_version: int,
    *,
    calibrate: bool = True,
) -> tuple[float, dict]:
    """
    Returns (score_on_0_to_10, params_dict)

    If calibrate=False, returns the pre-calibration (raw) score.
    """
    if score_version == 1:
        raw = (total_likes / total_possible) * 10.0 if total_possible > 0 else 0.0
        params = {"formula": "likes / possible * 10"}

    elif score_version == 2:
        raw = ((total_likes - total_dislikes) / total_possible) * 10.0 if total_possible > 0 else 0.0
        params = {"formula": "(likes - dislikes) / possible * 10"}

    elif score_version == 3:
        mu = _global_prior_mean()
        raw = ((total_likes + BAYESIAN_ALPHA * mu) / (total_possible + BAYESIAN_ALPHA)) * 10.0 if total_possible > 0 else 0.0
        params = {
            "formula": "(likes + α·μ) / (possible + α) * 10",
            "alpha": BAYESIAN_ALPHA,
            "mu": round(mu, 4),
        }

    elif score_version == 4:
        # v4: participation-friendly bonus on top of v3
        mu = _global_prior_mean()
        base = ((total_likes + BAYESIAN_ALPHA * mu) / (total_possible + BAYESIAN_ALPHA)) * 10.0 if total_possible > 0 else 0.0
        # Bonus: β * min(S / Smax, 1) * 10
        s_capped = min(int(total_submissions), int(V4_SMAX))
        boost = V4_BETA * (s_capped / float(V4_SMAX)) * 10.0
        raw = base + boost
        params = {
            "formula": "v3 + β * min(S/Smax, 1) * 10",
            "alpha": BAYESIAN_ALPHA,
            "mu": round(mu, 4),
            "beta": V4_BETA,
            "Smax": V4_SMAX,
            "base_v3": round(base, 3),
            "submissions": int(total_submissions),
        }

    else:
        raise ValueError(f"Unknown SCORING_VERSION: {score_version}")

    if not calibrate:
        # Return raw (optionally you can clamp here too, but better to keep truly raw)
        return float(raw), params

    # Calibrated path
    score = round(float(raw), 1)
    if CALIBRATE_OUTPUT:
        score = round(_calibrate(score, score_version), 1)
    score = max(0.0, min(10.0, score))  # clamp to [0,10]
    return score, params


def compute_drop_cred(user_id: int, score_version: int | None = None) -> dict:
    version = score_version if score_version is not None else SCORING_VERSION

    total_likes, total_dislikes = _likes_and_dislikes_for_user(user_id)
    total_possible = _total_possible_for_user(user_id)
    total_submissions = (
        db.session.query(func.count(Submission.id))
        .filter(Submission.user_id == user_id)
        .scalar()
        or 0
    )

    drop_cred_score, params = _apply_formula(
        total_likes, total_dislikes, total_possible, total_submissions, version, calibrate=True
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


def recompute_and_store_drop_cred(
    user_id: int, score_version: int | None = None, commit: bool = True
) -> DropCred:
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


def snapshot_user_all_versions(
    user_id: int, versions=(1, 2, 3, 4), commit: bool = True, replace: bool = False
):
    """
    Refresh drop_creds rows for a single user across the given versions.
    If replace=True, overwrite existing 'lifetime' rows for those versions.
    """
    if replace:
        db.session.query(DropCred).filter(
            DropCred.user_id == user_id,
            DropCred.score_version.in_(versions),
            DropCred.window_label == "lifetime",
        ).delete(synchronize_session=False)

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


# --- Calibration (0–10) -----------------------------------------------------
CALIBRATE_OUTPUT = True
CAL_TARGET_MEAN = 5.0
CAL_TARGET_STD  = 2.0

# simple per-process cache (recomputed on each snapshot run)
_CAL_CACHE: dict[int, tuple[float, float]] = {}


def _raw_stats_for_version(version: int) -> tuple[float, float]:
    """Compute mean and population std of RAW (pre-calibration) scores across all users."""
    user_ids = [uid for (uid,) in db.session.query(User.id).all()]
    raws: list[float] = []
    for uid in user_ids:
        L, D = _likes_and_dislikes_for_user(uid)
        P = _total_possible_for_user(uid)
        S = db.session.query(func.count(Submission.id)).filter(Submission.user_id == uid).scalar() or 0
        raw, _ = _apply_formula(L, D, P, S, version, calibrate=False)
        raws.append(float(raw))
    if not raws:
        return 0.0, 0.0
    mu = sum(raws) / len(raws)
    var = sum((x - mu) ** 2 for x in raws) / len(raws)  # population variance
    return mu, var ** 0.5


def _latest_raw_stats_for_version(version: int) -> tuple[float, float]:
    """Return (mean,std) for RAW scores; cached per process to avoid recompute within one run."""
    if version not in _CAL_CACHE:
        _CAL_CACHE[version] = _raw_stats_for_version(version)
    return _CAL_CACHE[version]


def _calibrate(raw: float, version: int) -> float:
    mu, sd = _latest_raw_stats_for_version(version)
    if sd <= 1e-6:  # too few users or no spread
        return max(0.0, min(10.0, raw))  # no-op clamp
    z = (raw - mu) / sd
    calibrated = CAL_TARGET_MEAN + z * CAL_TARGET_STD
    return max(0.0, min(10.0, calibrated))