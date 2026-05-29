"""recipe_template_allergens association table

Revision ID: p_recipe_template_allergens
Revises: o_halal_status_recipe_templates
Create Date: 2026-05-22

"""
from alembic import op
import sqlalchemy as sa


revision = 'p_recipe_template_allergens'
down_revision = 'o_halal_status_recipe_templates'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'recipe_template_allergens',
        sa.Column('recipe_template_id', sa.Integer(), nullable=False),
        sa.Column('allergen_type_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['allergen_type_id'], ['allergen_types.id']),
        sa.ForeignKeyConstraint(['recipe_template_id'], ['recipe_templates.id']),
        sa.PrimaryKeyConstraint('recipe_template_id', 'allergen_type_id'),
    )


def downgrade():
    op.drop_table('recipe_template_allergens')
