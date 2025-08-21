"""SET NULL creator_id; CASCADE DropCred.user_id; ensure CASCADEs

Revision ID: 1e1d53b72db7
Revises: d8e7ad29d2d4
Create Date: 2025-08-21 14:29:52.288056

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1e1d53b72db7'
down_revision = 'd8e7ad29d2d4'
branch_labels = None
depends_on = None


def _drop_fk_if_exists(table, column, referred_table):
    """Find and drop the actual FK for table.column -> referred_table.id (Postgres)."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return  # handled by batch ops elsewhere if needed

    fk_name = bind.execute(sa.text("""
        SELECT con.conname
        FROM pg_constraint con
        JOIN pg_class tbl ON tbl.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = tbl.relnamespace
        JOIN pg_attribute att ON att.attrelid = tbl.oid AND att.attnum = ANY (con.conkey)
        JOIN pg_class rt ON rt.oid = con.confrelid
        WHERE con.contype = 'f'
          AND nsp.nspname = current_schema()
          AND tbl.relname = :table
          AND att.attname = :column
          AND rt.relname = :ref
        LIMIT 1
    """), {"table": table, "column": column, "ref": referred_table}).scalar()

    if fk_name:
        op.drop_constraint(fk_name, table, type_="foreignkey")


def _recreate_fk(table, col, ref_table, new_name, ondelete=None):
    """Drop existing FK (if any) and create a new one with optional ondelete."""
    _drop_fk_if_exists(table, col, ref_table)
    op.create_foreign_key(
        new_name,
        table, ref_table,
        [col], ["id"],
        ondelete=ondelete
    )


def upgrade():
    # --- sound_circles.creator_id → ON DELETE SET NULL + nullable=True ---
    _drop_fk_if_exists("sound_circles", "creator_id", "users")

    with op.batch_alter_table("sound_circles") as batch:
        batch.alter_column("creator_id", existing_type=sa.Integer(), nullable=True)

    op.create_foreign_key(
        "fk_sound_circles__creator_id__users",
        "sound_circles", "users",
        ["creator_id"], ["id"],
        ondelete="SET NULL"
    )

    # --- drop_creds.user_id → ON DELETE CASCADE ---
    _recreate_fk("drop_creds", "user_id", "users",
                 "fk_drop_creds__user_id__users", ondelete="CASCADE")

    # --- Ensure CASCADEs everywhere they should be ---
    _recreate_fk("circle_memberships", "user_id",   "users",
                 "fk_circle_memberships__user_id__users", ondelete="CASCADE")
    _recreate_fk("circle_memberships", "circle_id", "sound_circles",
                 "fk_circle_memberships__circle_id__sound_circles", ondelete="CASCADE")

    _recreate_fk("submissions", "user_id",   "users",
                 "fk_submissions__user_id__users", ondelete="CASCADE")
    _recreate_fk("submissions", "circle_id", "sound_circles",
                 "fk_submissions__circle_id__sound_circles", ondelete="CASCADE")

    _recreate_fk("song_feedback", "user_id", "users",
                 "fk_song_feedback__user_id__users", ondelete="CASCADE")
    _recreate_fk("song_feedback", "song_id", "submissions",
                 "fk_song_feedback__song_id__submissions", ondelete="CASCADE")


def downgrade():
    # Best-effort rollback: drop our known names and recreate without ON DELETE actions.
    def _safe_drop(name, table):
        try:
            op.drop_constraint(name, table, type_="foreignkey")
        except Exception:
            pass

    # Drop known names
    _safe_drop("fk_song_feedback__user_id__users", "song_feedback")
    _safe_drop("fk_song_feedback__song_id__submissions", "song_feedback")
    _safe_drop("fk_submissions__user_id__users", "submissions")
    _safe_drop("fk_submissions__circle_id__sound_circles", "submissions")
    _safe_drop("fk_circle_memberships__user_id__users", "circle_memberships")
    _safe_drop("fk_circle_memberships__circle_id__sound_circles", "circle_memberships")
    _safe_drop("fk_drop_creds__user_id__users", "drop_creds")
    _safe_drop("fk_sound_circles__creator_id__users", "sound_circles")

    # Recreate plain FKs (no ON DELETE)
    op.create_foreign_key("fk_song_feedback__user_id__users",
                          "song_feedback", "users", ["user_id"], ["id"])
    op.create_foreign_key("fk_song_feedback__song_id__submissions",
                          "song_feedback", "submissions", ["song_id"], ["id"])

    op.create_foreign_key("fk_submissions__user_id__users",
                          "submissions", "users", ["user_id"], ["id"])
    op.create_foreign_key("fk_submissions__circle_id__sound_circles",
                          "submissions", "sound_circles", ["circle_id"], ["id"])

    op.create_foreign_key("fk_circle_memberships__user_id__users",
                          "circle_memberships", "users", ["user_id"], ["id"])
    op.create_foreign_key("fk_circle_memberships__circle_id__sound_circles",
                          "circle_memberships", "sound_circles", ["circle_id"], ["id"])

    op.create_foreign_key("fk_drop_creds__user_id__users",
                          "drop_creds", "users", ["user_id"], ["id"])

    # creator_id: leave nullable=True in downgrade to avoid failing if NULLs exist.
    # If you *must* restore NOT NULL, first UPDATE any NULLs to a valid user id.
    with op.batch_alter_table("sound_circles") as batch:
        batch.alter_column("creator_id", existing_type=sa.Integer(), nullable=True)
    op.create_foreign_key("fk_sound_circles__creator_id__users",
                          "sound_circles", "users", ["creator_id"], ["id"])