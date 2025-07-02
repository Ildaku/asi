from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import subprocess

# Создаем и настраиваем приложение Flask
app = Flask(__name__, instance_relative_config=True)

# Настройка строки подключения к базе данных
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/planner2.db'

app.config.from_mapping(
    SECRET_KEY='your-secret-key-should-be-changed',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Создаем объект db и связываем его с приложением
db = SQLAlchemy(app)

# Инициализируем систему миграций
migrate = Migrate(app, db)

# Инициализируем Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

# Применяем миграции при инициализации (только на сервере)
if DATABASE_URL:
    with app.app_context():
        try:
            print("Applying database migrations...")
            subprocess.run(['alembic', '-c', 'migrations/alembic.ini', 'upgrade', 'head'], check=True)
            print("Migrations applied successfully")
        except subprocess.CalledProcessError as e:
            print(f"Migration failed: {e}")
        except FileNotFoundError:
            print("Alembic not found, skipping migrations")

# Импортируем маршруты и модели в самом конце, чтобы избежать циклических ошибок
from . import routes, models