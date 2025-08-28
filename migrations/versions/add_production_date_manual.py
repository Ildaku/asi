"""Add production_date field to ProductionPlan

Revision ID: add_production_date_manual
Revises: c1234567890a
Create Date: 2025-08-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_production_date_manual'
down_revision = 'c1234567890a'  # ID последней миграции
branch_labels = None
depends_on = None

def upgrade():
    # Добавляем поле production_date
    op.add_column('production_plans', sa.Column('production_date', sa.DateTime(timezone=True), nullable=True))

def downgrade():
    # Убираем поле production_date
    op.drop_column('production_plans', 'production_date') 