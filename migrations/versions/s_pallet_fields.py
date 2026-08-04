"""add pallet_type and kg_per_pallet to production_plans

Revision ID: s_pallet_fields
Revises: r_shortfall_reason
Create Date: 2026-08-04

"""
from alembic import op
import sqlalchemy as sa


revision = 's_pallet_fields'
down_revision = 'r_shortfall_reason'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'production_plans',
        sa.Column('pallet_type', sa.String(length=20), nullable=True),
    )
    op.add_column(
        'production_plans',
        sa.Column('kg_per_pallet', sa.Float(), nullable=True),
    )


def downgrade():
    op.drop_column('production_plans', 'kg_per_pallet')
    op.drop_column('production_plans', 'pallet_type')
