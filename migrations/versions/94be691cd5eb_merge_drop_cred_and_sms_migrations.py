"""merge drop_cred and sms migrations

Revision ID: 94be691cd5eb
Revises: 156caecbb12b, ab5d31c65312
Create Date: 2025-08-15 10:28:13.375942

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94be691cd5eb'
down_revision = ('156caecbb12b', 'ab5d31c65312')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
