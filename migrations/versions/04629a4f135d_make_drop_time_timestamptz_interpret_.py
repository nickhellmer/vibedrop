"""make drop_time timestamptz (interpret existing as America/New_York)

Revision ID: 04629a4f135d
Revises: 716e651d170f
Create Date: 2025-08-12 20:36:16.883166

"""
# migration file
from alembic import op
import sqlalchemy as sa

revision = "XXXX_timestamptz_drop_time"
down_revision = "<your_previous_revision>"

def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("""
            ALTER TABLE sound_circles
            ALTER COLUMN drop_time
            TYPE timestamptz
            USING drop_time AT TIME ZONE 'America/New_York';
        """)
    else:
        with op.batch_alter_table("sound_circles") as b:
            b.alter_column(
                "drop_time",
                existing_type=sa.DateTime(timezone=False),
                type_=sa.DateTime(timezone=True),
                existing_nullable=False,
            )

def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("""
            ALTER TABLE sound_circles
            ALTER COLUMN drop_time
            TYPE timestamp
            USING (drop_time AT TIME ZONE 'UTC');
        """)
    else:
        with op.batch_alter_table("sound_circles") as b:
            b.alter_column(
                "drop_time",
                existing_type=sa.DateTime(timezone=True),
                type_=sa.DateTime(timezone=False),
                existing_nullable=False,
            )
