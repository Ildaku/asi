"""add_pending_approval_to_planstatus_enum

Revision ID: j1234567890h
Revises: i1234567890g
Create Date: 2026-05-12 12:00:00.000000

Добавляет значение PENDING_APPROVAL в PostgreSQL enum planstatus
(совпадает с SQLAlchemy Enum(PlanStatus) на проде).
"""
from alembic import op


revision = "j1234567890h"
down_revision = "i1234567890g"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Используем $migration$ чтобы не конфликтовать с shell $$ при копировании команд.
    op.execute(
        """
        DO $migration$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_enum
                WHERE enumtypid = 'planstatus'::regtype
                  AND enumlabel = 'PENDING_APPROVAL'
            ) THEN
                ALTER TYPE planstatus ADD VALUE 'PENDING_APPROVAL';
            END IF;
        END
        $migration$;
        """
    )


def downgrade():
    # Удаление значения из PostgreSQL enum без пересоздания типа не поддерживается простым ALTER.
    pass
