# def get_terms_from_text(text):
#     # Используем регулярное выражение для разделения по любым пробельным символам
#     terms = re.split(r'\s*\n\s*', text.strip())

#     # Удаление пустых строк
#     terms = [term for term in terms if term]

#     return terms

# URL API HH для получения справочника профессиональных ролей
HH_PROF_ROLES_URL = "https://api.hh.ru/professional_roles"

# API HH: справочник городов
HH_API_CITIES_URL = "https://api.hh.ru/areas"

# API ЦБ РФ: курсы валют
CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"

# Файл базы данных
DB_FILE = "hh-vacancies.db"

vacancies_file='AI_DS_vacancies.json'
vacancies_csv='AI_DS_vacancies.csv'
professions_csv='AI_DS_professions.csv'
salary_by_prof_file = 'AI_DS_salary_professions.csv'

file_descriptions = "AI_DS_descriptions.csv"
bad_descriptions_file = "AI_DS_bad_descriptions.csv"
ML_key_skills_file = 'AI_DS_key_skills.csv'

VACANCY_URL= "https://api.hh.ru/vacancies"
REQUIREMENTS_PATTERN = 'Требования|плюсом|жд[ёе]м|Ожида|ХОТИМ ВИДЕТЬ|важн|Require|кандидат|знани|навык|пожелани|опыт|умения|будем рады|компетенции|каким видим|рассмотреть|желательно|ценим|нужен|идеал|понадобится|skill|скил|Обязанности|Задачи|Чем предстоит заниматься|ждем|ожидаем|Summary of position|требуется|о задачах'

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

PROVERBS = """
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

# SEARCH_QUERY1 = 'NAME: (ML OR DS OR NLP OR LLM OR ИИ OR AI) AND (программист OR инженер OR разработчик OR тимлид OR аналитик OR analyst OR engineer OR developer)'
# SEARCH_QUERY2 = 'NAME: "дата сайнтист" OR "data scientist"'
# SEARCH_QUERY3 = 'NAME: Nlp OR "DS engineer" OR "AI developer" OR "AI engineer" OR "Data Scientist" OR "ML developer"'

# search_text = """
# NLP
# LLM
# Data Scientist
# DS engineer
# промпт инженер
# prompt engineer
# computer vision
# speech recognition
# Deep Learning
# Robotics Engineer
# AI Engineer
# AI developer
# ML developer
# ML Engeneer
# MLOps Engineer
# """

# prof_roles_text = """
# Руководитель группы разработки
# Дата-сайентист
# Программист, разработчик
# Тестировщик
# Руководитель проектов
# Аналитик
# Технический писатель
# BI-аналитик
# Менеджер продукта
# Учитель, преподаватель, педагог
# DevOps-инженер
# Архитектор
# Системный инженер
# Другое
# """

# terms = get_terms_from_text(search_text)
# print(terms)

# prof_roles_list = get_terms_from_text(prof_roles_text)
# print(prof_roles_list)

# # Заключение в кавычки и объединение через " OR "
# quoted_terms = [f'"{term}"' for term in terms]
# search_query = ' OR '.join(quoted_terms)
# search_query = f'NAME:{search_query}'

# print(search_query)