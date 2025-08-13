# services/scoring.py
from datetime import datetime
from sqlalchemy import func
from models import db, Submission, SongFeedback, CircleMembership, DropCred

LIKE_VALUE = "like"
DISLIKE_VALUE = "dislike"
TESTING_MODE = True  # Switch for local single-user testing

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

    print(f"[DropCred DEBUG] user={user_id} likes={likes} dislikes={dislikes}")
    return likes or 0, dislikes or 0


def _total_possible_for_user(user_id: int) -> int:
    """
    Count the total number of possible likes the user could have received
    based on the number of members in each circle they submitted to.
    """
    subs = db.session.query(Submission.id, Submission.circle_id)\
                     .filter_by(user_id=user_id).all()
    
    if not subs:
        print(f"[DropCred DEBUG] user={user_id} has no submissions")
        return 0

    circle_ids = [cid for _, cid in subs]
    members_by_circle = {
        cid: db.session.query(CircleMembership)
                       .filter_by(circle_id=cid)
                       .count()
        for cid in set(circle_ids)
    }

    print(f"[DropCred DEBUG] user={user_id} submissions -> {subs}")
    print(f"[DropCred DEBUG] circle_ids involved -> {circle_ids}")
    print(f"[DropCred DEBUG] members_by_circle -> {members_by_circle}")

    total_possible = 0
    for sid, cid in subs:
        member_count = members_by_circle.get(cid, 0)
        if TESTING_MODE:
            possible_for_drop = member_count  # include self
        else:
            possible_for_drop = max(0, member_count - 1)  # exclude self
        total_possible += possible_for_drop
        print(f"[DropCred DEBUG] sid={sid} cid={cid} member_count={member_count} possible_for_drop={possible_for_drop}")

    print(f"[DropCred DEBUG] user={user_id} TOTAL_POSSIBLE={total_possible}")
    return total_possible


def compute_drop_cred(user_id: int) -> dict:
    """
    Compute the Drop Cred score for a given user.
    """
    total_likes, total_dislikes = _likes_and_dislikes_for_user(user_id)
    total_possible = _total_possible_for_user(user_id)

    drop_cred_score = (total_likes / total_possible * 10) if total_possible > 0 else 0.0

    result = {
        "user_id": user_id,
        "total_likes": total_likes,
        "total_dislikes": total_dislikes,
        "total_possible": total_possible,
        "drop_cred_score": round(drop_cred_score, 1),
        "computed_at": datetime.utcnow(),
        "score_version": 1,
        "params": {
            "formula": "likes/possible*10",
            "possible_method": (
                "members_minus_self" if not TESTING_MODE else "members_including_self"
            )
        },
        "window_label": "lifetime",
        "window_start": None,
        "window_end": None
    }

    print(f"[DropCred DEBUG] result -> {result}")
    return result


def recompute_and_store_drop_cred(user_id: int, commit: bool = True) -> DropCred:
    """
    Compute and optionally store a snapshot in drop_creds.
    """
    data = compute_drop_cred(user_id)
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