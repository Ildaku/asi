#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления нового пользователя в систему
"""

from app import app, db
from app.models import User, UserRole

def add_new_user():
    """Добавляет нового пользователя в систему"""
    with app.app_context():
        print("=== Создание нового пользователя ===\n")
        
        # Ввод данных пользователя
        username = input("Введите логин пользователя: ").strip()
        if not username:
            print("❌ Логин не может быть пустым")
            return
        
        # Проверяем, не существует ли уже пользователь
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"❌ Пользователь с логином '{username}' уже существует")
            return
        
        # Ввод email
        email = input("Введите email пользователя: ").strip()
        if not email:
            print("❌ Email не может быть пустым")
            return
        
        # Проверяем уникальность email
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            print(f"❌ Пользователь с email '{email}' уже существует")
            return
        
        # Ввод пароля
        password = input("Введите пароль: ").strip()
        if not password:
            print("❌ Пароль не может быть пустым")
            return
        
        # Подтверждение пароля
        password_confirm = input("Подтвердите пароль: ").strip()
        if password != password_confirm:
            print("❌ Пароли не совпадают")
            return
        
        # Выбор роли
        print("\nДоступные роли:")
        print("1. ADMIN - полные права (управление пользователями, рецептурами, всем)")
        print("2. OPERATOR - ограниченные права (создание планов, управление замесами)")
        print("3. MANAGER - только «Для менеджеров» и «Годовое планирование» (просмотр)")
        
        while True:
            role_choice = input("\nВыберите роль (1, 2 или 3): ").strip()
            if role_choice == "1":
                role = UserRole.ADMIN
                role_name = "ADMIN"
                break
            elif role_choice == "2":
                role = UserRole.OPERATOR
                role_name = "OPERATOR"
                break
            elif role_choice == "3":
                role = UserRole.MANAGER
                role_name = "MANAGER"
                break
            else:
                print("❌ Введите 1, 2 или 3")
        
        # Создание пользователя
        try:
            new_user = User(
                username=username,
                email=email,
                role=role,
                is_active=True
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            print(f"\n✅ Пользователь '{username}' успешно создан!")
            print(f"📧 Email: {email}")
            print(f"🔑 Роль: {role_name}")
            print(f"🔐 Пароль: {password}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка при создании пользователя: {e}")
            return
        
        print(f"\n💡 Теперь можно войти в систему под логином '{username}' и паролем '{password}'")

def list_users():
    """Показывает список всех пользователей"""
    with app.app_context():
        print("\n=== Список пользователей в системе ===")
        users = User.query.all()
        
        if not users:
            print("Пользователей пока нет")
            return
        
        print(f"{'ID':<3} {'Логин':<15} {'Email':<25} {'Роль':<10} {'Активен':<8}")
        print("-" * 70)
        
        for user in users:
            status = "Да" if user.is_active else "Нет"
            print(f"{user.id:<3} {user.username:<15} {user.email:<25} {user.role:<10} {status:<8}")

def main():
    """Главная функция"""
    print("🚀 Скрипт управления пользователями")
    print("=" * 40)
    
    while True:
        print("\nВыберите действие:")
        print("1. Добавить нового пользователя")
        print("2. Показать список пользователей")
        print("3. Выход")
        
        choice = input("\nВведите номер действия (1-3): ").strip()
        
        if choice == "1":
            add_new_user()
        elif choice == "2":
            list_users()
        elif choice == "3":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Введите 1, 2 или 3")

if __name__ == '__main__':
    main() 