import requests
import sqlite3
import re
import time
import random
from datetime import datetime
from constants import *

def random_delay(min_seconds=10, max_seconds=15):
    """Устанавливает случайную задержку между min_seconds и max_seconds."""
    delay = random.randint(min_seconds, max_seconds)
    print(f"Задержка: {delay} секунд")
    time.sleep(delay)
    print(f"Продолжаем...")

# Глобальный словарь с курсами валют
exchange_rates = {}

def get_exchange_rates():
    """Загружает курсы валют из API ЦБ РФ и сохраняет в глобальном словаре exchange_rates."""
    global exchange_rates  # Разрешаем изменять глобальную переменную

    try:
        response = requests.get(CBR_API_URL)
        response.raise_for_status()
        data = response.json()["Valute"]

        exchange_rates = {currency: data[currency]["Value"] for currency in data}
        exchange_rates["RUB"] = 1  # Рубль всегда 1
        exchange_rates["RUR"] = 1  # Рубль всегда 1
        exchange_rates["BYR"] = exchange_rates["BYN"]  # Старый белорусский рубль

        print("✅ Курсы валют загружены:", exchange_rates)

    except requests.RequestException as e:
        print(f"❌ Ошибка загрузки курсов валют: {e}")
        exchange_rates = {}
 
def get_vacancies_by_query(search_query="ML", areas=["1"], professional_roles = [73,96,104,107],per_page=100):
                           
    """Получает список вакансий из API HH."""
    vacancies = []
    page = 0

    print(f'--------------------- Ключ: {search_query}')
    while True:
        params = {
            "text": f"{search_query}",
            "area": areas,
            "per_page": per_page,
            "page": page,
        }

        # Генерируем корректный список кортежей
        role_params = [("professional_role", role) for role in professional_roles]

        # Складываем два списка кортежей чтобы совместить словарь с уникальными ключами и список кортежей с повторяющимися ключами
        response = requests.get(VACANCY_URL, params=list(params.items()) + role_params)
        # print("GET-запрос:", response.url)

        response.raise_for_status()
        data = response.json()
        vacancies_list = data.get("items", [])
        vacancies.extend(vacancies_list)

        if page >= data.get("pages", 1) - 1:
            break
        page += 1

    print(f'Ключ: {search_query}, всего найдено {len(vacancies)}')

    # Извлекаем id и уникализируем список
    unique_ids  = {v["id"] for v in vacancies}
    
    print(f'Из них уникальных {len(unique_ids)}')
    return unique_ids

# Список User-Agent из популярных браузеров (можно расширить)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
    # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Safari/604.1",
    # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0",
    # "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    # "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/16.1 Mobile Safari/537.36",
    # "Mozilla/5.0 (iPad; CPU OS 15_5 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/15.5 Mobile Safari/537.36",
    # "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
]

# Дополнительные HTTP-заголовки, имитирующие браузерный запрос
ACCEPT_HEADERS = [
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    # "application/json, text/plain, */*",
    # "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
]

LANG_HEADERS = [
    # "en-US,en;q=0.5",
    "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    # "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
]

def get_full_vacancy_data(vacancy_id):
    """Получает полное описание вакансии из API HH."""

    vacancy_url = f"https://api.hh.ru/vacancies/{vacancy_id}"

    headers = {
    "User-Agent": random.choice(USER_AGENTS),  # Выбираем случайный User-Agent
    "Accept": random.choice(ACCEPT_HEADERS),   # Меняем заголовки Accept
    "Accept-Language": random.choice(LANG_HEADERS),  # Имитация локализации браузера
    "Referer": "https://hh.ru/",  # Маскировка источника запроса
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    }
    
    try:

        # response = requests.get(vacancy_url, headers=headers, timeout=10)
        response = requests.get(vacancy_url)
        if response.status_code == 200:
            return response.json(), response.status_code
        else:
            print(f"Не удалось получить данные. Статус: {response.status_code}")
            return None, response.status_code
    except requests.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None, response.status_code

def get_terms_from_description(description):

    # Шаг 1: Извлечение раздела "Требования"
    pattern = REQUIREMENTS_PATTERN
    requirements_section = re.findall(
        rf"<(?:h2|strong|div)[^>]*>[^<]*?(?:{pattern})[^<]*?</(?:h2|strong|div)>\s*(.*?)\s*(?=(?:<(?:h2|strong|div)[^>]*>|$))",
        description,
        re.DOTALL | re.IGNORECASE
    )

    # Шаг 2: Извлекаем булеты с требованиями
    if requirements_section:
        raw_list_items = []
        for section_text in requirements_section:
            # Извлечение текста внутри <li> или <p> для каждого раздела
            raw_list_items.extend(re.findall(r"(?:<li>|<p>)(.*?)(?:</li>|</p>)", section_text, re.DOTALL))
    else:
        return []
    
    # Шаг 3: Очистка текста от html тегов
    cleaned_items = [re.sub(r"<.*?>", "", item).strip() for item in raw_list_items]

    # Шаг 4: Поиск терминов
    terms = []
    for line in cleaned_items:
        terms += re.findall(r"\b(?:[A-Za-z0-9]*[A-Za-z]+[A-Za-z0-9]*)(?:[-\s][A-Za-z0-9]*[A-Za-z]+[A-Za-z0-9]*)*\b", line)

    return list(set(terms))

def save_vacancy_to_db(vacancy_data):
    """Сохраняет вакансию в базу данных, включая город, профессиональные роли и ключевые навыки."""
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()

        vacancy_id = vacancy_data["id"]
        name = vacancy_data.get("name", "Не указано")
        date_time = datetime.strptime(vacancy_data.get("published_at", ""), "%Y-%m-%dT%H:%M:%S%z").timestamp()
        
        salary = vacancy_data.get("salary", {})
        
        if salary:
            # Если зарплата указана, извлекаем данные, иначе присваиваем None
            currency = salary.get("currency")

            currency_rate = exchange_rates[currency]
            
            # Проверяем оля От, До на пустые значения. Если непустые, переводим в рубли
            salary_from = salary.get("from")
            if salary_from: salary_from *=  currency_rate
            salary_to = salary.get("to")
            if salary_to: salary_to *= currency_rate

        else:
            salary_from = None
            salary_to = None                  
        
        # Сохраняем вакансию
        cursor.execute("""
            INSERT INTO vacancies (id, Vacanciy_name, Date_time, Salary_from, Salary_to)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET 
                Vacanciy_name = excluded.Vacanciy_name,
                Date_time = excluded.Date_time,
                Salary_from = excluded.Salary_from,
                Salary_to = excluded.Salary_to;
        """, (vacancy_id, name, date_time, salary_from, salary_to))

        # Связываем вакансию с городами
        city_id = vacancy_data.get("area", {}).get("id")
        if city_id:
            cursor.execute("INSERT OR IGNORE INTO cities (id, name) VALUES (?, ?)", (city_id, vacancy_data["area"]["name"]))
            cursor.execute("INSERT OR IGNORE INTO vacancy_city (Vacancy_ID, City_ID) VALUES (?, ?)", (vacancy_id, city_id))

        # Извлекаем профессиональные роли (из поля `professional_roles`)
        professional_roles = vacancy_data.get("professional_roles", [])
        for role in professional_roles:
            role_id = role["id"]
            role_name = role["name"]
            
            cursor.execute("INSERT OR IGNORE INTO roles (id, name) VALUES (?, ?)", (role_id, role_name))
            cursor.execute("INSERT OR IGNORE INTO vacancy_role (Vacancy_ID, Role_ID) VALUES (?, ?)", (vacancy_id, role_id))

        # Извлекаем ключевые навыки
        skills = [skill["name"] for skill in vacancy_data.get("key_skills", [])]
        description = vacancy_data.get("description", "")
        extracted_terms = get_terms_from_description(description)
        unique_terms = list(set(skills + extracted_terms))

        # Сохраняем навыки в `Key_Skills`
        for term in unique_terms:
            cursor.execute("INSERT OR IGNORE INTO Key_skills (Skill_name) VALUES (?)", (term,))

            # Получаем ID навыка
            cursor.execute("SELECT id FROM Key_skills WHERE Skill_name = ?", (term,))
            skill_id = cursor.fetchone()[0]

            # Записываем в промежуточную таблицу
            cursor.execute("INSERT OR IGNORE INTO Vacancy_Keyskill (Vacancy_id, Keyskill_id) VALUES (?, ?)", (vacancy_id, skill_id))

    # print(f"\r✅ Вакансия {vacancy_id} сохранена.")

def get_saved_vacancies():
    """Получает список id вакансий из базы и возвращает их в виде множества."""
    
    with get_db_connection() as conn:  
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM vacancies")
        return {row[0] for row in cursor.fetchall()}  # Возвращаем множество


def process_vacancies(search_query="DS", areas=["1"], prof_roles = [73,96,104,107]):
    """Загружает вакансии и сохраняет их в базу с преобразованием валют в рубли."""

    get_exchange_rates()

    unique_id = get_vacancies_by_query(search_query, areas, prof_roles) # Получаем список id вакансий в базе
    unique_id = {int(uid) for uid in unique_id}  # Приводим к int
    saved_ids = get_saved_vacancies()
    to_process_id = unique_id - saved_ids  # Разность множеств

    print(f'Найдено {len(unique_id)} вакансий. Из них новых {len(to_process_id)}')

    # обрабатываем только свежие вакансии
    processed_count = 0

    while len(to_process_id):
        
        #  закачиваем по одной полной вакансии    
        vacancy_id = to_process_id.pop()

        # Получаем полное описание вакансии
        full_data,status_code = get_full_vacancy_data(vacancy_id)

        # Парсим пока нас не выкинули

        if status_code == 403:
                        
            random_delay(30,35) # Опасаемся санкций HH   
            to_process_id.add(vacancy_id)    # Возвращаем незагруженный УРЛ в множество  
            continue

        elif status_code == 404:

            print('Вакансия {vacancy_url} удалена')
            continue

        elif status_code == 200:

            processed_count += 1            
            # Сохраняем вакансию в БД
            save_vacancy_to_db(full_data)
            if processed_count % 115 == 0: # Эмпирическое число 120 после которого парсинг блокируется на 30 сек
                print(f'{len(to_process_id)} - осталось. Добавлено {processed_count}')
                random_delay(1,5) # Упреждающая задержка воизбежание блокировки

        else:

            print('Неизвестная ошибка. Код ответа: {status_code}')

    return unique_id            

def main():
    """Запускает процесс сбора вакансий и их анализа."""

    ids = process_vacancies(search_query="DS", areas=["1"], prof_roles = [73,96,104,107])
    print (f'Найдено {len(ids)} вакансий')

if __name__ == "__main__":
    main()
