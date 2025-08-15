#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для очистки "висящих" ссылок на удалённое сырьё
"""

from app import app, db
from app.models import MaterialBatch, BatchMaterial, ProductionBatch, ProductionPlan, RawMaterial
from sqlalchemy import text

def cleanup_orphaned_references():
    """Очищает все 'висящие' ссылки на удалённое сырьё"""
    
    with app.app_context():
        print("🔧 Начинаю очистку 'висящих' ссылок...")
        print("=" * 50)
        
        try:
            # 1. Находим MaterialBatch с несуществующим сырьём
            print("\n📊 Поиск MaterialBatch без сырья...")
            orphaned_mb = db.session.execute(text("""
                SELECT mb.id, mb.material_id, mb.batch_number, mb.quantity
                FROM material_batches mb
                LEFT JOIN raw_materials rm ON mb.material_id = rm.id
                WHERE rm.id IS NULL
            """)).fetchall()
            
            print(f"   Найдено: {len(orphaned_mb)} MaterialBatch без сырья")
            if orphaned_mb:
                for mb in orphaned_mb:
                    # Проверяем, есть ли ссылки на этот MaterialBatch
                    has_references = db.session.execute(text("""
                        SELECT COUNT(*) FROM batch_materials 
                        WHERE material_batch_id = :mb_id
                    """), {"mb_id": mb.id}).scalar()
                    
                    ref_status = f" (имеет {has_references} ссылок)" if has_references > 0 else " (без ссылок)"
                    print(f"   - ID: {mb.id}, material_id: {mb.material_id}, партия: {mb.batch_number}, количество: {mb.quantity}{ref_status}")
            
            # 2. Находим BatchMaterial с несуществующими MaterialBatch ИЛИ с MaterialBatch без сырья
            print("\n📊 Поиск BatchMaterial с проблемными MaterialBatch...")
            orphaned_bm = db.session.execute(text("""
                SELECT bm.id, bm.material_batch_id, bm.batch_id, bm.quantity
                FROM batch_materials bm
                LEFT JOIN material_batches mb ON bm.material_batch_id = mb.id
                WHERE mb.id IS NULL OR mb.material_id IS NULL
            """)).fetchall()
            
            print(f"   Найдено: {len(orphaned_bm)} BatchMaterial с проблемными MaterialBatch")
            if orphaned_bm:
                for bm in orphaned_bm:
                    # Определяем тип проблемы
                    if bm.material_batch_id:
                        mb_info = db.session.execute(text("""
                            SELECT mb.material_id, mb.batch_number 
                            FROM material_batches mb 
                            WHERE mb.id = :mb_id
                        """), {"mb_id": bm.material_batch_id}).fetchone()
                        
                        if mb_info:
                            problem_type = "без сырья" if mb_info.material_id is None else "не найден"
                            print(f"   - ID: {bm.id}, material_batch_id: {bm.material_batch_id}, batch_id: {bm.batch_id}, количество: {bm.quantity} (MaterialBatch {problem_type})")
                        else:
                            print(f"   - ID: {bm.id}, material_batch_id: {bm.material_batch_id}, batch_id: {bm.batch_id}, количество: {bm.quantity} (MaterialBatch не найден)")
                    else:
                        print(f"   - ID: {bm.id}, material_batch_id: {bm.material_batch_id}, batch_id: {bm.batch_id}, количество: {bm.quantity} (material_batch_id = NULL)")
            
            # 3. Находим ProductionBatch с несуществующими планами
            print("\n📊 Поиск ProductionBatch без планов...")
            orphaned_pb = db.session.execute(text("""
                SELECT pb.id, pb.plan_id, pb.batch_number, pb.weight
                FROM production_batches pb
                LEFT JOIN production_plans pp ON pb.plan_id = pp.id
                WHERE pp.id IS NULL
            """)).fetchall()
            
            print(f"   Найдено: {len(orphaned_pb)} ProductionBatch без планов")
            if orphaned_pb:
                for pb in orphaned_pb:
                    print(f"   - ID: {pb.id}, plan_id: {pb.plan_id}, партия: {pb.batch_number}, вес: {pb.weight}")
            
            # 4. Подсчитываем общее количество проблем
            # Считаем только те MaterialBatch, которые можно удалить (без ссылок)
            deletable_mb_count = 0
            for mb in orphaned_mb:
                has_references = db.session.execute(text("""
                    SELECT COUNT(*) FROM batch_materials 
                    WHERE material_batch_id = :mb_id
                """), {"mb_id": mb.id}).scalar()
                if has_references == 0:
                    deletable_mb_count += 1
            
            total_problems = deletable_mb_count + len(orphaned_bm) + len(orphaned_pb)
            
            if total_problems == 0:
                print("\n🎉 Проблем не обнаружено! Все ссылки корректны.")
                return
            
            print(f"\n⚠️  Всего найдено проблем: {total_problems}")
            print(f"   - MaterialBatch для удаления: {deletable_mb_count}")
            print(f"   - BatchMaterial для удаления: {len(orphaned_bm)}")
            print(f"   - ProductionBatch для удаления: {len(orphaned_pb)}")
            
            # 5. Запрашиваем подтверждение
            print("\n" + "=" * 50)
            print("🚨 ВНИМАНИЕ! Следующие действия нельзя отменить!")
            print("=" * 50)
            
            confirm = input(f"\nУдалить {total_problems} проблемных записей? (yes/no): ").strip().lower()
            
            if confirm != 'yes':
                print("❌ Операция отменена пользователем")
                return
            
            # 6. Выполняем очистку
            print("\n🧹 Начинаю очистку...")
            
            # Удаляем BatchMaterial с проблемными MaterialBatch
            if orphaned_bm:
                print(f"   Удаляю {len(orphaned_bm)} BatchMaterial с проблемными MaterialBatch...")
                for bm in orphaned_bm:
                    db.session.execute(text("DELETE FROM batch_materials WHERE id = :id"), {"id": bm.id})
                print("   ✅ BatchMaterial очищены")
            
            # Удаляем MaterialBatch с несуществующим сырьём (только те, на которые не ссылаются BatchMaterial)
            if orphaned_mb:
                print(f"   Удаляю MaterialBatch без ссылок...")
                deleted_mb_count = 0
                for mb in orphaned_mb:
                    # Проверяем, есть ли ссылки на этот MaterialBatch
                    has_references = db.session.execute(text("""
                        SELECT COUNT(*) FROM batch_materials 
                        WHERE material_batch_id = :mb_id
                    """), {"mb_id": mb.id}).scalar()
                    
                    if has_references == 0:
                        db.session.execute(text("DELETE FROM material_batches WHERE id = :id"), {"id": mb.id})
                        deleted_mb_count += 1
                    else:
                        print(f"     ⚠️  MaterialBatch ID {mb.id} имеет {has_references} ссылок, пропускаю")
                
                print(f"   ✅ Удалено MaterialBatch: {deleted_mb_count}")
            
            # Удаляем ProductionBatch с несуществующими планами
            if orphaned_pb:
                print(f"   Удаляю {len(orphaned_pb)} ProductionBatch...")
                for pb in orphaned_pb:
                    db.session.execute(text("DELETE FROM production_batches WHERE id = :id"), {"id": pb.id})
                print("   ✅ ProductionBatch очищены")
            
            # 7. Сохраняем изменения
            db.session.commit()
            print(f"\n🎉 Очистка завершена успешно!")
            print(f"   Удалено записей: {total_problems}")
            print(f"   - MaterialBatch: {deleted_mb_count}")
            print(f"   - BatchMaterial: {len(orphaned_bm)}")
            print(f"   - ProductionBatch: {len(orphaned_pb)}")
            
            # 8. Проверяем результат
            print("\n🔍 Проверяю результат...")
            remaining_mb = db.session.execute(text("""
                SELECT COUNT(*) FROM material_batches mb
                LEFT JOIN raw_materials rm ON mb.material_id = rm.id
                WHERE rm.id IS NULL
            """)).scalar()
            
            remaining_bm = db.session.execute(text("""
                SELECT COUNT(*) FROM batch_materials bm
                LEFT JOIN material_batches mb ON bm.material_batch_id = mb.id
                WHERE mb.id IS NULL
            """)).scalar()
            
            remaining_pb = db.session.execute(text("""
                SELECT COUNT(*) FROM production_batches pb
                LEFT JOIN production_plans pp ON pb.plan_id = pp.id
                WHERE pp.id IS NULL
            """)).scalar()
            
            print(f"   Оставшихся проблем: {remaining_mb + remaining_bm + remaining_pb}")
            
            if remaining_mb + remaining_bm + remaining_pb == 0:
                print("   ✅ Все проблемы устранены!")
            else:
                print("   ⚠️  Остались некоторые проблемы")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка при очистке: {e}")
            print("   Изменения отменены (rollback)")

def check_current_status():
    """Проверяет текущий статус проблем"""
    
    with app.app_context():
        print("🔍 Проверка текущего статуса...")
        print("=" * 30)
        
        try:
            # MaterialBatch без сырья
            orphaned_mb = db.session.execute(text("""
                SELECT COUNT(*) FROM material_batches mb
                LEFT JOIN raw_materials rm ON mb.material_id = rm.id
                WHERE rm.id IS NULL
            """)).scalar()
            
            # BatchMaterial с проблемными MaterialBatch
            orphaned_bm = db.session.execute(text("""
                SELECT COUNT(*) FROM batch_materials bm
                LEFT JOIN material_batches mb ON bm.material_batch_id = mb.id
                WHERE mb.id IS NULL OR mb.material_id IS NULL
            """)).scalar()
            
            # ProductionBatch без планов
            orphaned_pb = db.session.execute(text("""
                SELECT COUNT(*) FROM production_batches pb
                LEFT JOIN production_plans pp ON pb.plan_id = pp.id
                WHERE pp.id IS NULL
            """)).scalar()
            
            total = orphaned_mb + orphaned_bm + orphaned_pb
            
            print(f"MaterialBatch без сырья: {orphaned_mb}")
            print(f"BatchMaterial с проблемными MaterialBatch: {orphaned_bm}")
            print(f"ProductionBatch без планов: {orphaned_pb}")
            print(f"Всего проблем: {total}")
            
            if total == 0:
                print("🎉 Проблем не обнаружено!")
            else:
                print("⚠️  Обнаружены проблемы, требующие очистки")
                
        except Exception as e:
            print(f"❌ Ошибка при проверке: {e}")

def main():
    """Главная функция"""
    print("🚀 Скрипт очистки 'висящих' ссылок")
    print("=" * 40)
    
    while True:
        print("\nВыберите действие:")
        print("1. Проверить текущий статус")
        print("2. Выполнить очистку")
        print("3. Выход")
        
        choice = input("\nВведите номер действия (1-3): ").strip()
        
        if choice == "1":
            check_current_status()
        elif choice == "2":
            cleanup_orphaned_references()
        elif choice == "3":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Введите 1, 2 или 3")

if __name__ == '__main__':
    main() 