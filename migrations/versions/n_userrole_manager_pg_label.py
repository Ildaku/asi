"""add MANAGER label to userrole enum (PostgreSQL)

Revision ID: n_userrole_manager_pg_label
Revises: m_add_userrole_manager
Create Date: 2026-05-14

SQLAlchemy с native_enum для Python Enum передаёт в PostgreSQL **имя** члена
(MANAGER), а не UserRole.MANAGER.value. Метки ADMIN/OPERATOR уже в типе —
добавляем MANAGER.
"""
from alembic import op


revision = "n_userrole_manager_pg_label"
down_revision = "m_add_userrole_manager"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(
        """
        DO $migration$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = 'userrole' AND e.enumlabel = 'MANAGER'
                ) THEN
                    ALTER TYPE userrole ADD VALUE 'MANAGER';
                END IF;
            END IF;
        END
        $migration$;
        """
    )


def downgrade():
    pass
