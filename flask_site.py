from flask import Flask, render_template, request, g
from vacancies_analyze import get_hh_analytics
import random
from constants import * 

app = Flask(__name__)

cities_dict = {
    '1': 'Москва',
    '2': 'Санкт-Петербург',
    '1202': 'Новосибирск',
    '1261': 'Екатеринбург',
    '1438': 'Казань',
    '1042': 'Нижний Новгород',
    '1043': 'Челябинск',
    '1428': 'Самара',
    '1424': 'Омск',
    '1530': 'Ростов-на-Дону',
    '1384': 'Уфа',
    '1304': 'Красноярск',
    '1368': 'Пермь',
    '1376': 'Воронеж',
    '1216': 'Волгоград',
    'others': 'Прочие'
}

pv_text = """
Без труда не вытащишь и рыбку из пруда
Дело мастера боится
Терпение и труд всё перетрут
Работа дураков любит
Без дела жить – только небо коптить
Делу – время, потехе – час
Как потопаешь, так и полопаешь
Кто не работает, тот не ест
Семь раз отмерь – один раз отрежь
Маленькое дело лучше большого безделья
Глаза боятся, а руки делают
Без охоты нет работы
Семеро одного не ждут
Лентяю всегда праздник
Где руки и охота, там спорится работа
Не спеши языком, спеши делом
Работа не волк – в лес не убежит
"""

proverbs = pv_text.strip().splitlines()

# Функция подключения
def get_db():
    if "db" not in g:  # Проверяем, есть ли уже подключение
        g.db = get_db_connection()
        g.db.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по именам
    return g.db

# Закрываем соединение после запроса
@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def get_categories_dict():
    if "categories_dict" not in g:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories")
        categories = cursor.fetchall()
        g.categories_dict = {row["id"]: row["name"] for row in categories}  # Исправлен доступ по ключам
        cursor.close()

    return g.categories_dict

def get_roles_dict():
    if "roles_dict" not in g:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, category_id FROM roles")
        roles = cursor.fetchall()
        g.roles_dict = {row["id"]: {"name": row["name"], "category_id": row["category_id"]} for row in roles}
        cursor.close()

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