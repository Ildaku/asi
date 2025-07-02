from app import app, db
from app.models import RecipeItem
from sqlalchemy import Float

app.app_context().push()

# Проверяем тип поля в модели
print("Тип поля percentage в модели:", RecipeItem.__table__.columns['percentage'].type)

# Проверяем, является ли это Float без параметров
if isinstance(RecipeItem.__table__.columns['percentage'].type, Float):
    print("Это Float без указания точности")
    print("Параметры Float:", RecipeItem.__table__.columns['percentage'].type.__dict__)

# Тестируем сохранение точного значения
test_value = 8.925
print(f"\nТестируем сохранение значения: {test_value}")

# Создаем тестовый ингредиент
test_ingredient = RecipeItem(
    template_id=1,  # Предполагаем, что есть рецепт с ID=1
    material_type_id=1,  # Предполагаем, что есть тип сырья с ID=1
    percentage=test_value
)

try:
    db.session.add(test_ingredient)
    db.session.commit()
    print("✅ Значение успешно сохранено")
    
    # Проверяем, что сохранилось
    saved_ingredient = RecipeItem.query.filter_by(id=test_ingredient.id).first()
    print(f"Сохраненное значение: {saved_ingredient.percentage}")
    print(f"Тип сохраненного значения: {type(saved_ingredient.percentage)}")
    print(f"Точность сохранения: {saved_ingredient.percentage == test_value}")
    
    # Удаляем тестовый ингредиент
    db.session.delete(test_ingredient)
    db.session.commit()
    print("✅ Тестовый ингредиент удален")
    
except Exception as e:
    print(f"❌ Ошибка при сохранении: {e}")
    db.session.rollback() 