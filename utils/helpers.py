# utils/helpers.py

from datetime import datetime, timedelta

# --- Toggle for dev/testing behavior (e.g., scoring/debug prints) -------------
TESTING_MODE = True  # <-- Flip manually during development


# --- Cycle Date Logic --------------------------------------------------------

def get_current_cycle_date(circle):
    """
    Computes the key date for the current drop cycle.
    Logic depends on circle's drop frequency (daily/weekly/biweekly).
    Inputs:
        - circle (SoundCircle): includes frequency metadata (not yet modeled)
    Outputs:
        - A date object representing the current drop window
    """
    # TODO: Replace with dynamic logic once drop frequency is modeled
    today = datetime.now().date()
    return today  # Default to daily cycle for now


# Additional helper candidates (for future refactor):
# def get_user_circle(user_id):
# def validate_spotify_link(link):
# def get_feedback_summary(submission_id):
# etc.