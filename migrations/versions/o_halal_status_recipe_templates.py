"""add halal_status to recipe_templates

Revision ID: o_halal_status_recipe_templates
Revises: n_userrole_manager_pg_label
Create Date: 2026-05-22

"""
from alembic import op
import sqlalchemy as sa


revision = 'o_halal_status_recipe_templates'
down_revision = 'n_userrole_manager_pg_label'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute(
            """
            DO $migration$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'halalstatus') THEN
                    CREATE TYPE halalstatus AS ENUM ('haram', 'halal', 'not_specified');
                END IF;
            END
            $migration$;
            """
        )
    op.add_column(
        'recipe_templates',
        sa.Column('halal_status', sa.Enum('haram', 'halal', 'not_specified', name='halalstatus'), nullable=True),
    )


def downgrade():
    op.drop_column('recipe_templates', 'halal_status')
