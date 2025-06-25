from app import app, db
from app.models import ProductionPlan

def check_status():
    with app.app_context():
        plan = ProductionPlan.query.get(3)
        print(f"Current status: {plan.status}")

if __name__ == "__main__":
    check_status() 