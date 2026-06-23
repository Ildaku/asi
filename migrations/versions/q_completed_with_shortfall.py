"""add completed_with_shortfall to production_plans

Revision ID: q_completed_with_shortfall
Revises: p_recipe_template_allergens
Create Date: 2026-05-22

"""
from alembic import op
import sqlalchemy as sa


revision = 'q_completed_with_shortfall'
down_revision = 'p_recipe_template_allergens'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'production_plans',
        sa.Column('completed_with_shortfall', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade():
    op.drop_column('production_plans', 'completed_with_shortfall')
