from flask import Flask, render_template, request
import pandas as pd
from hh_parse import get_hh_analytics
import random

app = Flask(__name__)

roles_dict = {
    'all': 'Все',
    'developer': 'Разработчик',
    'dataScientist': 'Data scientist',
    'teamLead': 'Тимлид',
    'tester': 'Тестировщик'
}

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

@app.route("/")
def index():


    # return render_template('index.html', main_data=main_data, **context)
    return render_template('index.html', proverb = random.choice(proverbs))
    # return render_template('index.html', main_data=main_data, name='Leo', age=99)


@app.route('/contacts/')
def contacts():
    # где то взяли данные
    developer_name = 'Leo'
    # Контекст name=developer_name - те данные, которые мы передаем из view в шаблон
    # context = {'name': developer_name}
    # Словарь контекста context
    # return render_template('contacts.html', context=context)
    return render_template('contacts.html', name=developer_name, creation_date='16.01.2020')


# Роут, куда отправляются данные формы (метод POST)
@app.route('/results', methods=['POST'])
def results():
    query_string = request.form.get('queryString')
    role = request.form.get('professionalRole')   # напр., "developer"
    areas = request.form.getlist('areas')         # напр., ["1", "1261"]
    
    # Восстанавливаем названия:
    role_label = roles_dict.get(role, 'Неизвестная роль')
    areas_labels = [cities_dict.get(a, 'Неизвестный город') for a in areas]
    
    # Теперь можно собрать всё в словарь:
    param_dict = {
        "Название профессии": query_string,
        "Профессиональная роль": role_label,
        "Города": ", ".join(areas_labels) if areas_labels else "—"
    }

    # Получаем аналитику из бэкэнда - программа парсинга HH
    key_skills, df_salarys = get_hh_analytics(query_string=query_string,role=role,areas=areas)

    salary_html = df_salarys.to_html(classes="table table-striped table-bordered table-hover")
      
    # И передать в шаблон результатов:
    return render_template("results.html", 
                           param_dict=param_dict, 
                           key_skills=key_skills, 
                           salary_html = salary_html,
                           proverb = random.choice(proverbs))


@app.route('/form', methods=['GET'])
def form():
    return render_template('form.html', 
                           roles_dict=roles_dict, 
                           cities_dict=cities_dict,
                           proverb = random.choice(proverbs))


if __name__ == "__main__":
    app.run(debug=True)