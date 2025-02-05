import requests
from constants import *
from db import app, db
from models import Category, Role, City


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


def insert_roles_data(data):
    """Заполняет таблицы categories и roles, если они пусты."""
    if Category.query.count() > 0:
        print("Данные уже загружены. Пропускаем импорт.")
        return

    for category in data:
        category_obj = Category(id=category["id"], name=category["name"])
        db.session.add(category_obj)

        for role in category["roles"]:
            role_obj = Role(id=role["id"], name=role["name"], category_id=category["id"])
            db.session.add(role_obj)

    db.session.commit()
    print("✅ Роли успешно загружены в базу.")

def insert_cities_data(cities):
    """Заполняет таблицу cities, если она пуста."""
    if City.query.count() > 0:
        print("Данные о городах уже загружены. Пропускаем импорт.")
        return

    def insert_city(city, parent_id=None):
        city_obj = City(id=int(city["id"]), name=city["name"], parent_id=parent_id)
        db.session.add(city_obj)
        for subarea in city.get("areas", []):
            insert_city(subarea, int(city["id"]))

    for area in cities:
        insert_city(area)

    db.session.commit()
    print("✅ Города успешно загружены в базу.")


def init_db():
    """Основная функция: создает базу, таблицы и загружает данные."""
    
    with app.app_context():
        db.create_all()
        print("База данных успешно инициализирована.")
        
        # Загружаем и вставляем данные о профессиях
        roles_data = fetch_professional_roles()
        insert_roles_data(roles_data)

        # Загружаем и вставляем данные о городах
        cities_data = fetch_cities()
        insert_cities_data(cities_data)


if __name__ == "__main__":
    init_db()
