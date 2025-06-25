from app import app, db
from app.models import (
    ProductionPlan, RecipeTemplate, Product, RawMaterial, RawMaterialType, 
    MaterialBatch, BatchMaterial, RecipeItem
)
import warnings
from sqlalchemy.exc import SAWarning

# Игнорируем предупреждения о циклах в зависимостях, которые могут возникнуть при каскадном удалении
warnings.filterwarnings('ignore', r".*relationship.*will copy column .* to column .* which has a value.*", SAWarning)

def clear_database():
    """
    Полностью очищает все производственные данные из базы данных,
    оставляя только пользователей и структуру таблиц.
    """
    with app.app_context():
        print("Начинаю очистку базы данных...")

        # Удаляем в порядке зависимостей, чтобы избежать ошибок внешних ключей
        
        # 1. Удаляем все ингредиенты из замесов
        db.session.query(BatchMaterial).delete()
        print("- Записи об использованных ингредиентах удалены.")
        
        # 2. Удаляем все замесы (связанные с планами)
        # SQLAlchemy должен справиться с этим каскадно при удалении планов,
        # но для надежности можно сделать отдельно.
        
        # 3. Удаляем сами планы производства
        db.session.query(ProductionPlan).delete()
        print("- Планы производства удалены.")

        # 4. Удаляем ингредиенты из рецептур
        db.session.query(RecipeItem).delete()
        print("- Ингредиенты из рецептур удалены.")
        
        # 5. Удаляем сами рецептуры
        db.session.query(RecipeTemplate).delete()
        print("- Рецептуры удалены.")
        
        # 6. Удаляем продукты
        db.session.query(Product).delete()
        print("- Продукты удалены.")
        
        # 7. Удаляем партии сырья
        db.session.query(MaterialBatch).delete()
        print("- Партии сырья (MaterialBatch) удалены.")
        
        # 8. Удаляем сырье
        db.session.query(RawMaterial).delete()
        print("- Сырье (RawMaterial) удалено.")
        
        # 9. Удаляем типы сырья
        db.session.query(RawMaterialType).delete()
        print("- Типы сырья удалены.")

        try:
            db.session.commit()
            print("\nОчистка успешно завершена!")
            print("База данных готова для работы с чистого листа.")
        except Exception as e:
            db.session.rollback()
            print(f"\nПроизошла ошибка при очистке: {e}")

if __name__ == "__main__":
    # Спрашиваем подтверждение у пользователя
    confirm = input("Вы уверены, что хотите ПОЛНОСТЬЮ удалить все производственные данные (планы, продукты, сырье)? (yes/no): ")
    if confirm.lower() == 'yes':
        clear_database()
    else:
        print("Очистка отменена.") 