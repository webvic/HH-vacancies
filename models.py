from db import db

# Категории
class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)

# Профессиональные роли
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    category = db.relationship("Category", backref=db.backref("roles", cascade="all, delete"))

# Города
class City(db.Model):
    __tablename__ = "cities"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("cities.id", ondelete="CASCADE"), nullable=True)
    parent = db.relationship("City", remote_side=[id], backref="subcities")

# Вакансии
class Vacancy(db.Model):
    __tablename__ = "vacancies"
    id = db.Column(db.Integer, primary_key=True)
    vacancy_name = db.Column(db.String, nullable=False)
    date_time = db.Column(db.Integer, nullable=False)
    salary_from = db.Column(db.Float, nullable=True)
    salary_to = db.Column(db.Float, nullable=True)

    # ✅ Добавляем связь через таблицу `vacancy_city`
    cities = db.relationship(
        "City",
        secondary="vacancy_city",
        backref="vacancies"
    )

    # ✅ Добавляем связь через таблицу `vacancy_role`
    roles = db.relationship(
        "Role",
        secondary="vacancy_role",
        backref="vacancies"
    )

    # ✅ Добавляем связь через таблицу `vacancy_keyskill`
    key_skills = db.relationship(
        "KeySkill",
        secondary="vacancy_keyskill",
        backref="vacancies"
    )

# Промежуточная таблица: Вакансия - Город
vacancy_city = db.Table(
    "vacancy_city",
    db.Column("vacancy_id", db.Integer, db.ForeignKey("vacancies.id", ondelete="CASCADE"), primary_key=True),
    db.Column("city_id", db.Integer, db.ForeignKey("cities.id", ondelete="CASCADE"), primary_key=True)
)

# Промежуточная таблица: Вакансия - Роль
vacancy_role = db.Table(
    "vacancy_role",
    db.Column("vacancy_id", db.Integer, db.ForeignKey("vacancies.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
)

# Ключевые навыки
class KeySkill(db.Model):
    __tablename__ = "key_skills"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    skill_name = db.Column(db.String, unique=True, nullable=False)

# Промежуточная таблица: Вакансия - Ключевой навык
vacancy_keyskill = db.Table(
    "vacancy_keyskill",
    db.Column("vacancy_id", db.Integer, db.ForeignKey("vacancies.id", ondelete="CASCADE"), primary_key=True),
    db.Column("keyskill_id", db.Integer, db.ForeignKey("key_skills.id", ondelete="CASCADE"), primary_key=True)
)
