import sqlite3
import requests
import os
from constants import *
import os

def create_tables(conn):
    """Создает таблицы если их нет."""
    with conn:

        # Проф. категории
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );
        """)
        
        # Проф. роли
        conn.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                category_id INTEGER NOT NULL,
                FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
            );
        """)

        # Города
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                FOREIGN KEY(parent_id) REFERENCES cities(id) ON DELETE CASCADE
            );
        """)

        # Вакансии
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vacancies (
                id INTEGER PRIMARY KEY,
                Vacanciy_name TEXT,
                Date_time INTEGER,
                Salary_from REAL,
                Salary_to REAL
            );
        """)

        # Промежуточная таблица: Вакансия - Город
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vacancy_city (
                Vacancy_ID INTEGER NOT NULL,
                City_ID INTEGER NOT NULL,
                PRIMARY KEY (Vacancy_ID, City_ID),
                FOREIGN KEY (Vacancy_ID) REFERENCES vacancies(id) ON DELETE CASCADE,
                FOREIGN KEY (City_ID) REFERENCES cities(id) ON DELETE CASCADE
            );
        """)

        # Промежуточная таблица: Вакансия - Роль
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vacancy_role (
                Vacancy_ID INTEGER NOT NULL,
                Role_ID INTEGER NOT NULL,
                PRIMARY KEY (Vacancy_ID, Role_ID),
                FOREIGN KEY (Vacancy_ID) REFERENCES vacancies(id) ON DELETE CASCADE,
                FOREIGN KEY (Role_ID) REFERENCES roles(id) ON DELETE CASCADE
            );
        """)

        # Ключевые навыки
        conn.execute("""
            CREATE TABLE IF NOT EXISTS key_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Skill_name TEXT UNIQUE NOT NULL
            );
        """)

        # Промежуточная таблица: Вакансия - Ключевой навык
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vacancy_keyskill (
                Vacancy_id INTEGER NOT NULL,
                Keyskill_id INTEGER NOT NULL,
                PRIMARY KEY (Vacancy_id, Keyskill_id),
                FOREIGN KEY (Vacancy_id) REFERENCES vacancies(id) ON DELETE CASCADE,
                FOREIGN KEY (Keyskill_id) REFERENCES key_skills(id) ON DELETE CASCADE
            );
        """)

def fetch_professional_roles():
    """Загружает JSON с профессиональными ролями из API HH."""
    response = requests.get(HH_PROF_ROLES_URL)
    if response.status_code == 200:
        return response.json()["categories"]
    else:
        raise Exception(f"Ошибка загрузки данных: {response.status_code}")
    
def fetch_cities():
    """Загружает JSON с городами из API HH."""
    response = requests.get(HH_API_CITIES_URL)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Ошибка загрузки данных (города): {response.status_code}")


def insert_roles_data(conn, data):
    """Заполняет таблицы categories и roles, если они пусты."""
    with conn:
        # Проверяем, есть ли уже данные в таблицах
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM categories;")
        if cur.fetchone()[0] > 0:
            print("Данные уже загружены. Пропускаем импорт.")
            return

        for category in data:
            category_id = category["id"]
            category_name = category["name"]

            # Вставляем категорию
            conn.execute("INSERT INTO categories (id, name) VALUES (?, ?);", 
                         (category_id, category_name))

            for role in category["roles"]:
                role_id = role["id"]
                role_name = role["name"]

                # Вставляем роль
                conn.execute("INSERT OR IGNORE INTO roles (id, name, category_id) VALUES (?, ?, ?);",
                             (role_id, role_name, category_id))

        print("✅ Роли успешно загружены в базу.")

def insert_cities_data(conn, cities):
    """Заполняет таблицу cities, если она пуста."""
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM cities;")
        if cur.fetchone()[0] > 0:
            print("Данные о городах уже загружены. Пропускаем импорт.")
            return

        def insert_city(city, parent_id=None):
            conn.execute("INSERT OR IGNORE INTO cities (id, name, parent_id) VALUES (?, ?, ?);",
                         (int(city["id"]), city["name"], parent_id))
            for subarea in city.get("areas", []):
                insert_city(subarea, int(city["id"]))

        for area in cities:
            insert_city(area)

        print("✅ Города успешно загружены в базу.")        

def init_db():
    """Основная функция: создает базу, таблицы и загружает данные."""
    db_exists = os.path.exists(DB_FILE)
    conn = sqlite3.connect(DB_FILE)

    try:
        create_tables(conn)
        
        # Загружаем и вставляем данные о профессиях
        roles_data = fetch_professional_roles()
        insert_roles_data(conn, roles_data)

        # Загружаем и вставляем данные о городах
        cities_data = fetch_cities()
        insert_cities_data(conn, cities_data)

    finally:
        conn.close()

    if not db_exists:
        print(f"🎉 Создан файл базы данных: {DB_FILE}")

if __name__ == "__main__":
    init_db()
