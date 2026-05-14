"""merge multiple alembic heads (add_production_date_manual, f1234567890d, j1234567890h)

Revision ID: merge_heads_20260512
Revises: add_production_date_manual, f1234567890d, j1234567890h
Create Date: 2026-05-12

Объединяет три параллельные ветки миграций после c1234567890a, чтобы
`flask db upgrade head` снова имел одну голову.
"""


revision = "merge_heads_20260512"
down_revision = (
    "add_production_date_manual",
    "f1234567890d",
    "j1234567890h",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
