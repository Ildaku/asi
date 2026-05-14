"""Add production_date field to ProductionPlan

Revision ID: add_production_date_manual
Revises: c1234567890a
Create Date: 2025-08-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError


# revision identifiers, used by Alembic.
revision = 'add_production_date_manual'
down_revision = 'c1234567890a'  # ID последней миграции
branch_labels = None
depends_on = None


def _production_date_column_exists(connection) -> bool:
    if connection.dialect.name == 'postgresql':
        return bool(
            connection.execute(
                sa.text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = 'production_plans' "
                    "AND column_name = 'production_date')"
                )
            ).scalar()
        )
    inspector = sa.inspect(connection)
    names = {c['name'] for c in inspector.get_columns('production_plans')}
    return 'production_date' in names


def _is_duplicate_column_error(exc: ProgrammingError) -> bool:
    orig = getattr(exc, 'orig', None)
    if getattr(orig, 'pgcode', None) == '42701':
        return True
    msg = str(orig or exc).lower()
    return 'duplicate column' in msg


def upgrade():
    conn = op.get_bind()
    if _production_date_column_exists(conn):
        return
    try:
        op.add_column(
            'production_plans',
            sa.Column('production_date', sa.DateTime(timezone=True), nullable=True),
        )
    except ProgrammingError as e:
        if not _is_duplicate_column_error(e):
            raise


def downgrade():
    conn = op.get_bind()
    if not _production_date_column_exists(conn):
        return
    op.drop_column('production_plans', 'production_date')
