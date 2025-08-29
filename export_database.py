#!/usr/bin/env python3
"""
Скрипт для экспорта данных из базы данных Render
"""

import os
import json
from datetime import datetime
from app import app, db
from app.models import User, ProductionPlan, RawMaterial, Product, RecipeTemplate

def export_users():
    """Экспорт пользователей"""
    users = User.query.all()
    users_data = []
    
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value if user.role else None,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }
        users_data.append(user_data)
    
    return users_data

def export_production_plans():
    """Экспорт планов производства"""
    plans = ProductionPlan.query.all()
    plans_data = []
    
    for plan in plans:
        plan_data = {
            'id': plan.id,
            'product_id': plan.product_id,
            'template_id': plan.template_id,
            'quantity': plan.quantity,
            'batch_number': plan.batch_number,
            'status': plan.status.value if plan.status else None,
            'notes': plan.notes,
            'production_date': plan.production_date.isoformat() if plan.production_date else None,
            'created_at': plan.created_at.isoformat() if plan.created_at else None,
            'updated_at': plan.updated_at.isoformat() if plan.updated_at else None,
            'created_by': plan.created_by
        }
        plans_data.append(plan_data)
    
    return plans_data

def export_raw_materials():
    """Экспорт сырья"""
    materials = RawMaterial.query.all()
    materials_data = []
    
    for material in materials:
        material_data = {
            'id': material.id,
            'name': material.name,
            'type_id': material.type_id,
            'batch_number': material.batch_number,
            'quantity_kg': material.quantity_kg,
            'date_received': material.date_received.isoformat() if material.date_received else None,
            'expiration_date': material.expiration_date.isoformat() if material.expiration_date else None,
            'created_at': material.created_at.isoformat() if material.created_at else None,
            'updated_at': material.updated_at.isoformat() if material.updated_at else None
        }
        materials_data.append(material_data)
    
    return materials_data

def export_products():
    """Экспорт продуктов"""
    products = Product.query.all()
    products_data = []
    
    for product in products:
        product_data = {
            'id': product.id,
            'name': product.name,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None,
            'created_by': product.created_by
        }
        products_data.append(product_data)
    
    return products_data

def main():
    """Основная функция экспорта"""
    print("🚀 Начинаю экспорт данных из базы данных...")
    
    try:
        with app.app_context():
            # Экспортируем данные
            data = {
                'export_date': datetime.now().isoformat(),
                'users': export_users(),
                'production_plans': export_production_plans(),
                'raw_materials': export_raw_materials(),
                'products': export_products()
            }
            
            # Сохраняем в JSON файл
            filename = f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Экспорт завершён! Файл: {filename}")
            print(f"📊 Статистика:")
            print(f"   👥 Пользователи: {len(data['users'])}")
            print(f"   📋 Планы производства: {len(data['production_plans'])}")
            print(f"   🧱 Сырьё: {len(data['raw_materials'])}")
            print(f"   🏭 Продукты: {len(data['products'])}")
            
    except Exception as e:
        print(f"❌ Ошибка при экспорте: {e}")

if __name__ == "__main__":
    main() 