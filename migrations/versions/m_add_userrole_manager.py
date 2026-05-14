"""add MANAGER / manager to userrole enum (PostgreSQL)

Revision ID: m_add_userrole_manager
Revises: l_managers_fields_20260514
Create Date: 2026-05-14

В БД встречаются enum-метки в разном регистре (зависит от истории миграций).
Добавляем значение, совпадающее с UserRole.MANAGER.value = \"manager\".
"""
from alembic import op


revision = "m_add_userrole_manager"
down_revision = "l_managers_fields_20260514"
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
                    WHERE t.typname = 'userrole' AND e.enumlabel = 'manager'
                ) THEN
                    ALTER TYPE userrole ADD VALUE 'manager';
                END IF;
            END IF;
        END
        $migration$;
        """
    )


def downgrade():
    pass
