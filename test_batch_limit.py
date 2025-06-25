from app import app, db
from app.models import ProductionPlan, PlanStatus

with app.app_context():
    print("Проверка ограничений на вес замеса:")
    
    print("\nПроверка существующих планов и замесов:")
    plans = ProductionPlan.query.all()
    for plan in plans:
        print(f"План {plan.id}: {plan.quantity} кг")
        for batch in plan.batches:
            status = "✅ OK" if batch.weight <= 1000 else "❌ ПРЕВЫШЕНИЕ ЛИМИТА"
            print(f"  Замес {batch.batch_number}: {batch.weight} кг {status}")
    
    print(f"\nВсего планов: {len(plans)}")
    total_batches = sum(len(plan.batches) for plan in plans)
    print(f"Всего замесов: {total_batches}")
    
    # Проверяем, есть ли замесы с превышением лимита
    oversized_batches = []
    for plan in plans:
        for batch in plan.batches:
            if batch.weight > 1000:
                oversized_batches.append((plan.id, batch.batch_number, batch.weight))
    
    if oversized_batches:
        print(f"\n⚠️  Найдены замесы с превышением лимита 1000 кг:")
        for plan_id, batch_number, weight in oversized_batches:
            print(f"  План {plan_id}, Замес {batch_number}: {weight} кг")
    else:
        print(f"\n✅ Все замесы соответствуют лимиту 1000 кг") 