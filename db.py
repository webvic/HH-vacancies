from flask import g, Flask
from constants import DB_FILE
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text  # Используем `text()` для выполнения сырых SQL-запросов

app = Flask(__name__)

# Настройки подключения к БД
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_FILE}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Создаем объект SQLAlchemy
db = SQLAlchemy(app)

def check_database():
    """Проверяет подключение и таблицы в базе данных."""
    try:
        print(f"🔹 Подключение к базе данных: {db.engine.url}")

        # 1️⃣ Какие таблицы SQLAlchemy ожидает создать?
        print("🔹 Таблицы, которые SQLAlchemy ожидает создать:", list(db.metadata.tables.keys()))

        # 2️⃣ Какие таблицы реально есть в БД?
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result.fetchall()]
            print(f"🔹 Таблицы, которые есть в БД: {tables}")

        # 3️⃣ Проверяем колонки в `vacancies`
        with db.engine.connect() as connection:
            result = connection.execute(text("PRAGMA table_info(vacancies);"))
            columns = [row[1] for row in result.fetchall()]
            print(f"🔹 Колонки в `vacancies`: {columns}")

        # 4️⃣ Проверяем записи в `categories`
        from models import Category
        with app.app_context():
            count = db.session.query(Category).count()
            print(f"🔹 Записей в таблице `categories`: {count}")

    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")


# Если файл запускается отдельно, проверяем базу
if __name__ == "__main__":
    with app.app_context():
        check_database()

