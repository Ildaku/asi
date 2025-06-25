from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Создаем и настраиваем приложение Flask
app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY='your-secret-key-should-be-changed',
    # Указываем правильный путь к базе данных в папке instance
    SQLALCHEMY_DATABASE_URI='sqlite:///planner2.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Настройка строки подключения к базе данных
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/planner2.db'

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

# Импортируем маршруты и модели в самом конце, чтобы избежать циклических ошибок
from . import routes, models