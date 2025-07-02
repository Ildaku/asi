"""Change percentage to Numeric(6,3) in recipe_items

Revision ID: change_percentage_to_numeric_manual
Revises: b0dfb14a93c8
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'change_percentage_to_numeric_manual'
down_revision = 'b0dfb14a93c8'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite не поддерживает ALTER COLUMN TYPE напрямую
    # Поэтому создаем новую таблицу с правильным типом
    op.execute("""
        CREATE TABLE recipe_items_new (
            id INTEGER NOT NULL PRIMARY KEY,
            template_id INTEGER,
            material_type_id INTEGER,
            percentage NUMERIC(6, 3),
            created_at DATETIME,
            updated_at DATETIME,
            created_by INTEGER,
            FOREIGN KEY(template_id) REFERENCES recipe_templates (id),
            FOREIGN KEY(material_type_id) REFERENCES raw_material_types (id),
            FOREIGN KEY(created_by) REFERENCES users (id)
        )
    """)
    
    # Копируем данные из старой таблицы
    op.execute("""
        INSERT INTO recipe_items_new 
        SELECT id, template_id, material_type_id, percentage, created_at, updated_at, created_by
        FROM recipe_items
    """)
    
    # Удаляем старую таблицу
    op.execute("DROP TABLE recipe_items")
    
    # Переименовываем новую таблицу
    op.execute("ALTER TABLE recipe_items_new RENAME TO recipe_items")


def downgrade():
    # Возвращаем старый тип FLOAT
    op.execute("""
        CREATE TABLE recipe_items_old (
            id INTEGER NOT NULL PRIMARY KEY,
            template_id INTEGER,
            material_type_id INTEGER,
            percentage FLOAT,
            created_at DATETIME,
            updated_at DATETIME,
            created_by INTEGER,
            FOREIGN KEY(template_id) REFERENCES recipe_templates (id),
            FOREIGN KEY(material_type_id) REFERENCES raw_material_types (id),
            FOREIGN KEY(created_by) REFERENCES users (id)
        )
    """)
    
    # Копируем данные обратно
    op.execute("""
        INSERT INTO recipe_items_old 
        SELECT id, template_id, material_type_id, percentage, created_at, updated_at, created_by
        FROM recipe_items
    """)
    
    # Удаляем новую таблицу
    op.execute("DROP TABLE recipe_items")
    
    # Переименовываем старую таблицу
    op.execute("ALTER TABLE recipe_items_old RENAME TO recipe_items") 