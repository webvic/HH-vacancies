import json
import numpy as np
import pandas as pd
from hh_parse import save_vacancies_to_json
import xml.etree.ElementTree as ET
import requests
from constants import *

def get_cbr_exchange_rates():
    url = 'http://www.cbr.ru/scripts/XML_daily.asp'
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception('Не удалось получить данные от ЦБ РФ')
    
    root = ET.fromstring(response.content)
    exchange_rates = {}
    
    for valute in root.findall('Valute'):
        char_code = valute.find('CharCode').text
        nominal = int(valute.find('Nominal').text)
        value = float(valute.find('Value').text.replace(',', '.'))
        exchange_rates[char_code] = value / nominal  # Приводим к единичному курсу
    
    exchange_rates['RUB'] = 1.0  # Добавляем рубль
    
    print(exchange_rates)
    return exchange_rates

# Получение курсов
rates = get_cbr_exchange_rates()

# Открываем файл и загружаем JSON-данные
with open(vacancies_file, 'r', encoding='utf-8') as file:
    vacancies = json.load(file)

# Создаем список словарей
flat_vacancies = []

for vacancy in vacancies:
    flat_item = {
        "id": vacancy["id"],
        "name": vacancy["name"],
        "url": vacancy["url"],
        "professional_roles": [role["name"] for role in vacancy["professional_roles"]]
    }
    salary = vacancy["salary"]
    if salary:
        flat_item["salary_from"] = salary["from"]
        flat_item["salary_to"] = salary["to"]
        flat_item["currency"] = salary["currency"]
        flat_item["gross"] = salary["gross"]

    flat_vacancies.append(flat_item)
    prof_roles = vacancy["professional_roles"]

df_vacancies = pd.DataFrame(flat_vacancies)
df_vacancies.to_csv('raw_vac_file.csv')

# 4.1: Развертывание списка ролей в отдельные строки
df_vacancies = df_vacancies.explode('professional_roles')
print("\nDataFrame после развертывания ролей:")
print(df_vacancies[['professional_roles', 'salary_from', 'salary_to']])

# Шаг 2: Дропнем нерелевантные профессии с использованием isin()
df_vacancies = df_vacancies[df_vacancies['professional_roles'].isin(prof_roles_list)]

# Заполняем пропущенные значения от/до имеющимися значениями до/от
df_vacancies['salary_to'].fillna(df_vacancies['salary_from'], inplace=True)
df_vacancies['salary_from'].fillna(df_vacancies['salary_to'], inplace=True)
df_vacancies.to_csv('after_price_filling_vac_file.csv')

print(f'Найдено вакансий {len(df_vacancies)}')

# Подсчёт строк, где хотя бы одно из полей 'salary_from' или 'salary_to' не NaN
filled_salary_count = df_vacancies[['salary_from', 'salary_to']].notnull().any(axis=1).sum()

print(f"Количество вакансий с заполненными зарплатными полями: {filled_salary_count}")

# Получение курсов валют
exchange_rates = get_cbr_exchange_rates()

# Определяем колонки для конвертации
columns_to_convert = ['salary_from', 'salary_to']

# Проверка наличия всех валют в exchange_rates и дропаем пустые
unique_currencies = df_vacancies['currency'].dropna().unique()
missing_currencies = set(unique_currencies) - set(exchange_rates.keys())
if missing_currencies:
    print(f"Внимание! Отсутствуют курсы для валют: {missing_currencies}")
    # Можно решить, как обработать отсутствующие валюты. Например, заполнить курсом 1.0 или удалить такие строки
    # Для примера, заполним отсутствующие курсы значением np.nan
    for currency in missing_currencies:
        exchange_rates[currency] = 1.

# Создаём колонку курсов обмена для каждой строки
df_vacancies['exchange_rate'] = df_vacancies['currency'].map(exchange_rates)

# Конвертируем зарплаты в рубли, заменяя оригинальные значения
df_vacancies[columns_to_convert] = df_vacancies[columns_to_convert].multiply(df_vacancies['exchange_rate'], axis=0)

# Обновляем колонку 'currency' на 'RUB'
df_vacancies['currency'] = 'RUB'

# Удаляем временную колонку 'exchange_rate'
df_vacancies.drop('exchange_rate', axis=1, inplace=True)

print("\nDataFrame после конвертации в рубли:")
print(df_vacancies)

# Шаг 4: Расчёт среднего значения зарплат по всем ролям
average_salary_by_role = df_vacancies.groupby('professional_roles').agg(
    average_salary_from=pd.NamedAgg(column='salary_from', aggfunc='mean'),
    average_salary_to=pd.NamedAgg(column='salary_to', aggfunc='mean')
).dropna().reset_index()

print('----------- Сгруппировали по проф ролям -------------')
print(average_salary_by_role)

# Сортировка на месте
average_salary_by_role.sort_values(by='average_salary_to', ascending=False, inplace=True)
average_salary_by_role.reset_index(drop=True, inplace=True)

print("\nСредняя зарплата по всем проф. ролям:")
print(average_salary_by_role)

# Вычисление итоговых средних значений для столбцов 'Средняя зарплата от' и 'Средняя зарплата до'
average_salary_from_mean = average_salary_by_role['average_salary_from'].mean()
average_salary_to_mean = average_salary_by_role['average_salary_to'].mean()

# Создание DataFrame для итоговой строки
total_row = pd.DataFrame({
    'professional_roles': ['ИТОГО'],
    'average_salary_from': [average_salary_from_mean],
    'average_salary_to': [average_salary_to_mean]
})

# Добавление итоговой строки в основной DataFrame
average_salary_by_role = pd.concat([average_salary_by_role, total_row], ignore_index=True)

print("\nDataFrame после добавления итоговой строки 'ИТОГО':")
print(average_salary_by_role)

# Округление и преобразование столбцов в целые числа в одну строку
salary_columns = ['average_salary_from', 'average_salary_to']
average_salary_by_role[salary_columns] = (average_salary_by_role[salary_columns]/1000).round().astype(int)

# Переименование столбцов
average_salary_by_role.rename(columns={
    'professional_roles': 'Профессиональная роль',
    'average_salary_from': 'Средняя зарплата от (тыс. ₽)',
    'average_salary_to': 'Средняя зарплата до (тыс. ₽)'
}, inplace=True)

average_salary_by_role.to_csv (salary_by_prof_file)

print(average_salary_by_role)
