"""Mass renames (tables, columns, FKs) - scaffolding

Revision ID: 10e45ad2b0d2
Revises: 0695c42d37d7
Create Date: 2025-08-11 13:34:37.561856

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '10e45ad2b0d2'
down_revision = '0695c42d37d7'
branch_labels = None
depends_on = None


def upgrade():
    # --- Table renames only (data-preserving) ---
    op.rename_table('user', 'users')
    op.rename_table('sound_circle', 'sound_circles')
    op.rename_table('circle_membership', 'circle_memberships')
    op.rename_table('submission', 'submissions')
    op.rename_table('vibe_score', 'vibe_scores')
    # song_feedback already correct; no change

    # No column renames needed:
    # - submissions.visible_to_others already correct
    # - song_feedback.song_id stays as-is (FK -> submissions.id)


def downgrade():
    # Reverse table renames
    op.rename_table('vibe_scores', 'vibe_score')
    op.rename_table('submissions', 'submission')
    op.rename_table('circle_memberships', 'circle_membership')
    op.rename_table('sound_circles', 'sound_circle')
    op.rename_table('users', 'user')
