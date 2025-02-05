from flask import render_template, request, g
from models import Category, Role  # ✅ Импортируем модели ORM
from vacancies_analyze import get_hh_analytics
import random
from constants import * 
from db import app

proverbs = PROVERBS.strip().splitlines()

def get_categories_dict():
    """Возвращает словарь категорий, кешируя его в `g`."""
    if "categories_dict" not in g:
        categories = Category.query.all()  # ✅ Получаем все категории через SQLAlchemy ORM
        g.categories_dict = {category.id: category.name for category in categories}
    return g.categories_dict


def get_roles_dict():
    """Возвращает словарь ролей, кешируя его в `g`."""
    if "roles_dict" not in g:
        roles = Role.query.all()  # ✅ Получаем все роли через ORM
        g.roles_dict = {role.id: {"name": role.name, "category_id": role.category_id} for role in roles}
    return g.roles_dict

@app.route("/")
def index():

    # return render_template('index.html', main_data=main_data, **context)
    return render_template('index.html', proverb = random.choice(proverbs))
    # return render_template('index.html', main_data=main_data, name='Leo', age=99)

@app.route('/contacts/')
def contacts():
    # где то взяли данные
    developer_name = 'Виктор Щеблецов'
    # Контекст name=developer_name - те данные, которые мы передаем из view в шаблон
    # context = {'name': developer_name}
    # Словарь контекста context
    # return render_template('contacts.html', context=context)
    return render_template('contacts.html', name=developer_name, creation_date='16.01.2025')

# Роут, куда отправляются данные формы (метод POST)
@app.route('/results', methods=['POST'])
def results():
    query_string = request.form.get('queryString')
    roles = request.form.getlist('professionalRole')  # Получаем список выбранных ролей
    areas = request.form.getlist('areas')  # Получаем список выбранных городов
    
    # Восстанавливаем названия ролей и городов:
    roles_dict = get_roles_dict()
    roles_labels = [roles_dict.get(int(role), {"name": "Неизвестная роль"})["name"] for role in roles]
    areas_labels = [cities_dict.get(area, 'Неизвестный город') for area in areas]
    
    # Подготавливаем параметры для отображения
    param_dict = {
        "Название профессии": query_string,
        "Профессиональные роли": ", ".join(roles_labels) if roles_labels else "—",
        "Города": ", ".join(areas_labels) if areas_labels else "—"
    }

    # Вызываем функцию аналитики с массивами ролей и городов
    key_skills, df_salarys = get_hh_analytics(query_string=query_string, roles=roles, areas=areas)

    salary_html = df_salarys.to_html(classes="table table-striped table-bordered table-hover")

    # Передаем данные в шаблон `results.html`
    return render_template(
        "results.html",
        param_dict=param_dict,
        key_skills=key_skills,
        salary_html=salary_html,
        proverb=random.choice(proverbs)
    )

@app.route('/form', methods=['GET'])
def form():

    # 1️⃣ Загружаем категории
    categories_dict = get_categories_dict()

    # 2️⃣ Загружаем профессиональные роли и ссылки на категории
    roles_dict = get_roles_dict()

    # 3️⃣ Передаем данные в шаблон form.html
    return render_template(
        "form.html",
        categories_dict=categories_dict,  # Категории
        roles_dict=roles_dict,            # Профессиональные роли
        cities_dict=cities_dict,          # Города
        proverb=random.choice(proverbs)   # Случайная пословица
    )

if __name__ == "__main__":
    app.run(debug=True)