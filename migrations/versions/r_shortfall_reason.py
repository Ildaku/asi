"""add shortfall_reason to production_plans

Revision ID: r_shortfall_reason
Revises: q_completed_with_shortfall
Create Date: 2026-05-22

"""
from alembic import op
import sqlalchemy as sa


revision = 'r_shortfall_reason'
down_revision = 'q_completed_with_shortfall'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'production_plans',
        sa.Column('shortfall_reason', sa.String(length=500), nullable=True),
    )


def downgrade():
    op.drop_column('production_plans', 'shortfall_reason')
