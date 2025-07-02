from app import app
import subprocess
import os

if __name__ == '__main__':
    # Применяем миграции при запуске (только на сервере)
    if os.environ.get('DATABASE_URL'):
        try:
            print("Applying database migrations...")
            subprocess.run(['alembic', '-c', 'migrations/alembic.ini', 'upgrade', 'head'], check=True)
            print("Migrations applied successfully")
        except subprocess.CalledProcessError as e:
            print(f"Migration failed: {e}")
        except FileNotFoundError:
            print("Alembic not found, skipping migrations")
    
    app.run(debug=True) 