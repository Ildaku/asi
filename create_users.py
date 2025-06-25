from app import app, db
from app.models import User, UserRole

def create_initial_users():
    with app.app_context():
        # Проверяем, существует ли уже пользователь admin
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                role=UserRole.ADMIN
            )
            admin_user.set_password('Asi1527')
            db.session.add(admin_user)
            print("✅ Пользователь admin создан")
        else:
            print("ℹ️  Пользователь admin уже существует")

        # Проверяем, существует ли уже пользователь operator
        operator_user = User.query.filter_by(username='operator').first()
        if not operator_user:
            operator_user = User(
                username='operator',
                email='operator@example.com',
                role=UserRole.OPERATOR
            )
            operator_user.set_password('2022')
            db.session.add(operator_user)
            print("✅ Пользователь operator создан")
        else:
            print("ℹ️  Пользователь operator уже существует")

        try:
            db.session.commit()
            print("\n🎉 Пользователи успешно созданы!")
            print("\nДанные для входа:")
            print("Администратор:")
            print("  Логин: admin")
            print("  Пароль: Asi1527")
            print("\nОператор:")
            print("  Логин: operator")
            print("  Пароль: 2022")
        except Exception as e:
            print(f"❌ Ошибка при создании пользователей: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_initial_users() 