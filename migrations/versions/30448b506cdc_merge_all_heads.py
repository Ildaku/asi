"""merge_all_heads

Revision ID: 30448b506cdc
Revises: ('add_production_date_manual', 'f1234567890d', 'g1234567890e')
Create Date: 2025-01-20 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30448b506cdc'
down_revision = ('add_production_date_manual', 'f1234567890d', 'g1234567890e')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

