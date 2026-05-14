"""add_monthly_plans

Revision ID: f1234567890d
Revises: ae1fe6fc2a9d
Create Date: 2025-01-20 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError


# revision identifiers, used by Alembic.
revision = 'f1234567890d'
down_revision = 'e1234567890c'
branch_labels = None
depends_on = None


def _monthly_plans_table_exists(connection) -> bool:
    if connection.dialect.name == 'postgresql':
        return bool(
            connection.execute(
                sa.text("SELECT to_regclass('public.monthly_plans') IS NOT NULL")
            ).scalar()
        )
    inspector = sa.inspect(connection)
    return 'monthly_plans' in inspector.get_table_names()


def _monthly_plans_index_names(connection) -> set:
    inspector = sa.inspect(connection)
    if 'monthly_plans' not in inspector.get_table_names():
        return set()
    return {ix['name'] for ix in inspector.get_indexes('monthly_plans')}


def upgrade():
    conn = op.get_bind()
    if not _monthly_plans_table_exists(conn):
        try:
            op.create_table(
                'monthly_plans',
                sa.Column('id', sa.Integer(), nullable=False),
                sa.Column('year', sa.Integer(), nullable=False),
                sa.Column('month', sa.Integer(), nullable=False),
                sa.Column('product_id', sa.Integer(), nullable=False),
                sa.Column('template_id', sa.Integer(), nullable=False),
                sa.Column('quantity_kg', sa.Float(), nullable=False),
                sa.Column(
                    'created_at',
                    sa.DateTime(timezone=True),
                    server_default=sa.text('now()'),
                    nullable=True,
                ),
                sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
                sa.ForeignKeyConstraint(['product_id'], ['products.id']),
                sa.ForeignKeyConstraint(['template_id'], ['recipe_templates.id']),
                sa.PrimaryKeyConstraint('id'),
                sa.UniqueConstraint(
                    'year', 'month', 'product_id', name='unique_monthly_plan'
                ),
            )
        except ProgrammingError as e:
            if not _is_duplicate_relation_error(e):
                raise

    idx_name = op.f('ix_monthly_plans_id')
    if idx_name not in _monthly_plans_index_names(conn):
        try:
            op.create_index(idx_name, 'monthly_plans', ['id'], unique=False)
        except ProgrammingError as e:
            if not _is_duplicate_relation_error(e):
                raise


def _is_duplicate_relation_error(exc: ProgrammingError) -> bool:
    orig = getattr(exc, 'orig', None)
    if getattr(orig, 'pgcode', None) == '42P07':
        return True
    msg = str(orig or exc).lower()
    return 'already exists' in msg


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'monthly_plans' not in inspector.get_table_names():
        return

    idx_name = op.f('ix_monthly_plans_id')
    existing = {ix['name'] for ix in inspector.get_indexes('monthly_plans')}
    if idx_name in existing:
        op.drop_index(idx_name, table_name='monthly_plans')
    op.drop_table('monthly_plans')
