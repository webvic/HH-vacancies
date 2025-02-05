import pandas as pd
from constants import *
from hh_parse import process_vacancies
from sqlalchemy.orm import aliased
from models import *
from db import db

def get_salary_analytics(ids_found):
    """Считает вакансии и зарплаты, затем формирует DataFrame."""
    
    # Алиасы для удобства
    vr = aliased(vacancy_role)  # Промежуточная таблица "Вакансия - Роль"
    vks = aliased(vacancy_keyskill)  # Промежуточная таблица "Вакансия - Навык"

    # 1️⃣ Получаем данные через SQLAlchemy ORM
    results = (
        db.session.query(
            Role.name.label("Профессия"), 
            Vacancy.salary_from, 
            Vacancy.salary_to
        )
        .select_from(Vacancy)  # Явно указываем начальную таблицу
        .join(vr, Vacancy.id == vr.c.vacancy_id)  # vacancy_role (мост)
        .join(Role, vr.c.role_id == Role.id)  # roles
        .join(Category, Role.category_id == Category.id)  # categories
        .filter(Vacancy.id.in_(ids_found))  # Вместо temp_ids используем filter()
        .all()
    )

    # 2️⃣ Преобразуем результат в DataFrame
    df_vacancies = pd.DataFrame(results, columns=["Профессия", "Salary_from", "Salary_to"])
    
      # 3️⃣ Добавляем колонку "Средняя зарплата"
    df_vacancies["Salary_av"] = df_vacancies.apply(
        lambda row: (row["Salary_from"] + row["Salary_to"]) / 2 
        if pd.notnull(row["Salary_from"]) and pd.notnull(row["Salary_to"]) else
        row["Salary_from"] if pd.notnull(row["Salary_from"]) else
        row["Salary_to"], axis=1
    )

    # 4️⃣ Переводим зарплаты в тысячи ₽
    df_vacancies.loc[:, ["Salary_from", "Salary_to", "Salary_av"]] /= 1000
    print("Колонки в df_vacancies:", df_vacancies.columns.tolist())


    # 5️⃣ Группируем данные по профессиям (подсчет вакансий и зарплат)
    df_roles = df_vacancies.groupby("Профессия").agg(
        Вакансий_всего=("Профессия", "size"),  # ✔ Корректное создание колонки в agg()
        Вакансий_с_зп=("Salary_av", "count"),  # ✔ Правильное имя колонки
        Средн_зп_от=("Salary_from", "mean"),  # ✔ Теперь колонка существует
        Средн_зп_до=("Salary_to", "mean"),  # ✔ Теперь колонка существует
        Средн_зп=("Salary_av", "mean"),
        Медианная_зп=("Salary_av", "median")
    ).reset_index()

    # 6️⃣ Теперь загружаем **навыки отдельно** (чтобы не размножать вакансии)
    results = (
        db.session.query(
            Role.name.label("Профессия"),
            KeySkill.skill_name.label("Навык")
        )
        .select_from(Vacancy)  # Явно указываем начальную таблицу
        .join(vr, Vacancy.id == vr.c.vacancy_id)  # vacancy_role (мост)
        .join(Role, vr.c.role_id == Role.id)  # roles
        .join(Category, Role.category_id == Category.id)  # categories
        .join(vks, Vacancy.id == vks.c.vacancy_id)  # vacancy_keyskill (мост)
        .join(KeySkill, vks.c.keyskill_id == KeySkill.id)  # key_skills
        .filter(Vacancy.id.in_(ids_found))  # Вместо временной таблицы temp_ids
        .all()
    )

    # 2️⃣ Преобразуем результат в DataFrame
    df_skills = pd.DataFrame(results, columns=["Профессия", "Навык"])

    # 8️⃣ Считаем ТОП-5 навыков по профессиям
    df_skills_count = df_skills.groupby(["Профессия", "Навык"]).size().reset_index(name="Частота")
    df_skills_sorted = df_skills_count.sort_values(["Профессия", "Частота"], ascending=[True, False])
    
    top_skills_grouped = (
        df_skills_sorted.groupby("Профессия")["Навык"]
        .apply(lambda x: ", ".join(x.head(5)))  # Берем 5 самых популярных навыков
        .reset_index()
        .rename(columns={"Навык": "ТОП5 навыков"})
    )

    # 9️⃣ Объединяем таблицы
    df_roles = df_roles.merge(top_skills_grouped, on="Профессия", how="left")

    # 🔟 Подсчет ТОП-5 навыков для "ИТОГО"
    total_top_skills = ", ".join(
        df_skills_count.groupby("Навык")["Частота"]
        .sum()
        .reset_index()
        .sort_values("Частота", ascending=False)["Навык"]
        .head(5)
    )

    # 🔟 Добавляем строку "ИТОГО"
    total_row = pd.DataFrame([{
        "Профессия": "ИТОГО",
        "Вакансий_всего": df_roles["Вакансий_всего"].sum(),
        "Вакансий_с_зп": df_roles["Вакансий_с_зп"].sum(),
        "Средн_зп_от": df_vacancies["Salary_from"].mean(),
        "Средн_зп_до": df_vacancies["Salary_to"].mean(),
        "Средн_зп": df_vacancies["Salary_av"].mean(),
        "Медианная_зп": df_vacancies["Salary_av"].median(),
        "ТОП5 навыков": total_top_skills
    }])

    # 🔟 Объединяем с "ИТОГО" и округляем
    df_final = pd.concat([df_roles, total_row], ignore_index=True)

    df_final = df_final.rename(columns={
        "Вакансий_всего" : "Вакансий всего",
        "Вакансий_с_зп" : "Вакансий с з/п",
        "Средн_зп_от": "Средн з/п от, тыс. ₽",
        "Средн_зп_до": "Средн з/п до, тыс. ₽",
        "Средн_зп": "Средн з/п, тыс. ₽",
        "Медианная_зп": "Медианная з/п, тыс. ₽"
    })

    # Добавляем колонку "Вакансий с з/п (%)"
    df_final["% с з/п"] = df_final["Вакансий с з/п"] / df_final["Вакансий всего"] * 100

    # 🔟 Приводим к `int`, чтобы числа не печатались с `.0`
    numeric_columns = ["% с з/п", "Средн з/п от, тыс. ₽", "Средн з/п до, тыс. ₽", 
                       "Средн з/п, тыс. ₽", "Медианная з/п, тыс. ₽"]
    
    df_final = df_final.dropna()


    df_final[numeric_columns] = df_final[numeric_columns].fillna(0).round(0).astype(int)
    print(df_final)

    # Создаем текстовую колонку "Указана з/п"
    df_final["Указана з/п"] = df_final.apply(lambda row: f"{row['Вакансий с з/п']} ({row['% с з/п']}%)", axis=1)

    df_return = df_final[["Профессия", 
                          "Медианная з/п, тыс. ₽",
                          "Вакансий всего", 
                          "Указана з/п", 
                          "ТОП5 навыков" ]]
    
    df_sorted = df_return[:-1].sort_values(by="Вакансий всего", ascending=False)  # Сортируем все, кроме последней
    df_return = pd.concat([df_sorted, df_return[-1:]], ignore_index=True)  # Добавляем обратно последнюю строку

    return [skill.strip() for skill in total_top_skills.split(',')], df_return

def get_hh_analytics(query_string='ML', roles=[73,96,104,107,124,126,148], areas=['1']):
    ids_found = process_vacancies(search_query=query_string, areas=areas, prof_roles = roles)
    key_skills, df = get_salary_analytics(ids_found = ids_found)

    return key_skills, df

def main():
    key_skills, df = get_hh_analytics(roles=[])
    print(key_skills)
    print(df)

if __name__ == "__main__":
    main()            