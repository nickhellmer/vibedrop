"""Make SoundCircle.drop_time timezone-aware

Revision ID: 1ec04e5a971f
Revises: 10e45ad2b0d2
Create Date: 2025-08-12 19:32:53.091849

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1ec04e5a971f'
down_revision = '10e45ad2b0d2'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Convert to timestamptz and reinterpret existing naive values
        # as America/New_York local time (adjust if you actually stored UTC).
        op.execute(
            """
            ALTER TABLE sound_circles
            ALTER COLUMN drop_time
            TYPE timestamptz
            USING drop_time AT TIME ZONE 'America/New_York';
            """
        )
    else:
        # SQLite / others: alter type to timezone-aware DateTime
        with op.batch_alter_table("sound_circles") as batch_op:
            batch_op.alter_column(
                "drop_time",
                existing_type=sa.DateTime(timezone=False),
                type_=sa.DateTime(timezone=True),
                existing_nullable=False,
            )

    # ### end Alembic commands ###


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Convert back to timestamp without time zone; store UTC clock time as naive
        op.execute(
            """
            ALTER TABLE sound_circles
            ALTER COLUMN drop_time
            TYPE timestamp
            USING (drop_time AT TIME ZONE 'UTC');
            """
        )
    else:
        with op.batch_alter_table("sound_circles") as batch_op:
            batch_op.alter_column(
                "drop_time",
                existing_type=sa.DateTime(timezone=True),
                type_=sa.DateTime(timezone=False),
                existing_nullable=False,
            )

    # ### end Alembic commands ###
