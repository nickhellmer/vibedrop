"""make drop_time timestamptz interpreting current values as UTC

Revision ID: 716e651d170f
Revises: 1ec04e5a971f
Create Date: 2025-08-12 19:54:00.504004

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '716e651d170f'
down_revision = '1ec04e5a971f'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE sound_circles
        ALTER COLUMN drop_time
        TYPE timestamptz
        USING (drop_time AT TIME ZONE 'UTC');
    """)

def downgrade():
    op.execute("""
        ALTER TABLE sound_circles
        ALTER COLUMN drop_time
        TYPE timestamp
        USING (drop_time AT TIME ZONE 'UTC');
    """)
