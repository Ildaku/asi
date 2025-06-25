from app import app, db
from app.models import ProductionPlan

def update_statuses():
    with app.app_context():
        # Обновляем все планы со статусом "утвержден" на "утверждён"
        plans = ProductionPlan.query.filter_by(status="утвержден").all()
        for plan in plans:
            plan.status = "утверждён"
        db.session.commit()
        print(f"Обновлено планов: {len(plans)}")

if __name__ == "__main__":
    update_statuses() 