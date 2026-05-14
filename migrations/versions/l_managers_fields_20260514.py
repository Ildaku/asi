"""manager dashboard fields on production_plans

Revision ID: l_managers_fields_20260514
Revises: merge_heads_20260512
Create Date: 2026-05-14

"""
from alembic import op
import sqlalchemy as sa


revision = 'l_managers_fields_20260514'
down_revision = 'merge_heads_20260512'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'production_plans',
        sa.Column('manager_planned_production_date', sa.Date(), nullable=True),
    )
    op.add_column(
        'production_plans',
        sa.Column('handed_to_okk_date', sa.Date(), nullable=True),
    )
    op.add_column(
        'production_plans',
        sa.Column('actual_okk_check_date', sa.Date(), nullable=True),
    )
    op.add_column(
        'production_plans',
        sa.Column('okk_approved_on', sa.Date(), nullable=True),
    )


def downgrade():
    op.drop_column('production_plans', 'okk_approved_on')
    op.drop_column('production_plans', 'actual_okk_check_date')
    op.drop_column('production_plans', 'handed_to_okk_date')
    op.drop_column('production_plans', 'manager_planned_production_date')
