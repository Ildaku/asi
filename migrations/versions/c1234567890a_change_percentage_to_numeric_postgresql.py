"""Change percentage to Numeric(6,3) in recipe_items for PostgreSQL

Revision ID: change_percentage_to_numeric_postgresql
Revises: b0dfb14a93c8
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1234567890a'
down_revision = 'b0dfb14a93c8'
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL поддерживает ALTER COLUMN TYPE
    op.execute("ALTER TABLE recipe_items ALTER COLUMN percentage TYPE NUMERIC(6,3)")


def downgrade():
    # Возвращаем обратно к FLOAT
    op.execute("ALTER TABLE recipe_items ALTER COLUMN percentage TYPE FLOAT") 
