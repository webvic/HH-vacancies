import requests
from collections import Counter
import re
import pandas as pd
from bs4 import BeautifulSoup
import json
import os
import time
import random
from constants import *
from vacancies_analyze import get_salary_analytics

def random_delay(min_seconds=15, max_seconds=30):
    """
    Устанавливает случайную задержку между min_seconds и max_seconds.

    :param min_seconds: Минимальное количество секунд.
    :param max_seconds: Максимальное количество секунд.
    """
    delay = random.randint(min_seconds, max_seconds)
    print(f"Задержка: {delay} секунд")
    time.sleep(delay)
    print(f"Продолжаем...")

def save_vacancies_to_json(vacancies, vacancies_file="vacancies.json"):
    """
    Сохраняет список вакансий в JSON файл.

    :param vacancies: Список вакансий.
    :param file_name: Имя файла для сохранения.
    """
    with open(vacancies_file, "w", encoding="utf-8") as file:
        json.dump(vacancies, file, ensure_ascii=False, indent=4)

    return   vacancies_file      

def load_vacancies_from_json(vacancies_file=vacancies_file):
    """
    Загружает список вакансий из JSON файла.

    :param vacancies_file: Имя файла для загрузки.
    :return: Список вакансий или None, если файл не существует.
    """
    try:
        with open(vacancies_file, "r", encoding="utf-8") as file:
            vacancies = json.load(file)
        return vacancies
    except FileNotFoundError:
        print(f"Файл '{vacancies_file}' не найден.")
        return None

def get_vacancies_by_query(search_query=search_query, area=["1"], per_page=100):
    """
    Получает список вакансий из API HH по специализации.

    :param specialization_id: ID специализации.
    :param area: ID города (Москва = "1").
    :param per_page: Количество вакансий на странице.
    :return: Список вакансий.
    """
    vacancies = []
    page = 0
  

    print(f'--------------------- Ключ: {search_query}')
    while True:
        params = {
            "text": f"{search_query}",
            "area": area,
            "per_page": per_page,
            "page": page,
        }
        response = requests.get(VACANCY_URL, params=params)
        response.raise_for_status()
        data = response.json()
        vacancies_list = data.get("items", [])
        vacancies.extend(vacancies_list)
        for vacancy in vacancies_list[:5]:
            print(vacancy['name'],'\r')

        if page >= data.get("pages", 1) - 1:
            break
        page += 1
    print(f'Ключ: {search_query}, всего найдено {len(vacancies)}')    
  
    # Уникальные по ключу "id"
    unique_vacancies = []
    vacancies_names = set()
    seen_ids = set()

    for vacancy in vacancies:
        if vacancy["id"] not in seen_ids:
            seen_ids.add(vacancy["id"])
            unique_vacancies.append(vacancy)
            name = vacancy["name"]
            if name not in vacancies_names:
                vacancies_names.add(name)


    save_vacancies_to_json(vacancies, vacancies_file)
    print(f'Найдено {len(vacancies)} Из них уникальных {len(unique_vacancies)},\
          сохранены в файл {save_vacancies_to_json(vacancies, vacancies_file)}')
    return unique_vacancies

def get_full_vacancy_data(vacancy_url):
    """
    Получает полное описание вакансии из API HH.

    :param vacancy_url: URL вакансии.
    :return: Полное описание вакансии или None, если запрос неудачен.
    """
    try:
        response = requests.get(vacancy_url)
        if response.status_code == 200:
            return response.json(), response.status_code
        else:
            print(f"Не удалось получить данные. Статус: {response.status_code}")
            return None, response.status_code
    except requests.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None, response.status_code


def extract_strong_blocks(description):
    """
    Извлекает все блоки <strong> из текста.

    :param description: HTML-описание вакансии.
    :return: Список текстов внутри <strong> блоков.
    """
    # Декодируем HTML-символы
    soup = BeautifulSoup(description, "html.parser")

    # Извлекаем все теги <strong>
    strong_blocks = [tag.get_text(strip=True) for tag in soup.find_all("strong")]

    return strong_blocks    

def load_or_initialize_descriptions(file_descriptions):
    """
    Загружает словарь требований из CSV файла в DataFrame и преобразует в словарь, 
    если файл существует. Если файла нет, инициализирует пустой словарь.

    :param file_name: Имя CSV файла для загрузки.
    :return: Кортеж (словарь требований, следующий доступный ключ).
    """
    if os.path.exists(file_descriptions):
        # Загружаем CSV в DataFrame
        df = pd.read_csv(file_descriptions, index_col=0)
        # Преобразуем DataFrame в словарь
        requirements_dict = df["description"].to_dict()
        # Определяем последний ключ
        start_key = max(requirements_dict.keys())+1
    else:
        print(f"Файл '{file_descriptions}' не найден. Инициализируем пустой словарь.")
        requirements_dict = {}
        start_key = 0

    return requirements_dict, start_key

def get_unique_urls(vacancies):
    """
    Подсчитывает количество уникальных вакансий по их идентификаторам.

    :param vacancies: Список вакансий в формате JSON.
    :return: Количество уникальных вакансий.
    """
    unique_urls = set()
    
    for vacancy in vacancies:
        if 'url' in vacancy:  # Проверяем наличие ключа id
            unique_urls.add(vacancy['url'])
    
    return unique_urls

def get_terms_from_vacancies(vacancies):
    """ Берем список вакансий, открываем каждую и сохраняем поле "description в file_descriptions"""

    unique_urls = get_unique_urls(vacancies)
    print('Уникальных вакансий',len(unique_urls))
    
    all_descriptions = []
    bad_descriptionts = []
    ML_key_skills = []
    descr_count=0
    unique_urls_num=len(unique_urls)

    while len(unique_urls):
        #  закачиваем по одной полной вакансии, периодически сохраняем полученный файл
        print(f'{unique_urls_num} - осталось. Добавлено {len(all_descriptions)} \r')
        vacancy_url = unique_urls.pop()

        # Получаем полное описание вакансии
        full_data,status_code = get_full_vacancy_data(vacancy_url)

        # Парсим пока нас не выкинули

        if status_code == 403:
                        
            random_delay() # Опасаемся санкций HH   

            unique_urls.add(vacancy_url)    # Возвращаем незагруженный УРЛ в множество  

            continue

        elif status_code == 404:
            print('Вакансия {vacancy_url} удалена')
            continue
        elif status_code == 200:
            descr_count += 1            
            # Извлекаем описание
            description = full_data.get("description", "")
            if description:
                all_descriptions.append(description)
                terms =  get_terms_from_description(description, bad_descriptionts)
            else:
                terms = []
            # Извлекаем ключевые навыки
            key_skills = [skill["name"] for skill in full_data.get("key_skills", [])]
            
            # Объединаем и уникализируем списки явных и извлеченных навыков
            unique_terms = list(set(terms + key_skills))
            ML_key_skills.extend(unique_terms)
        else:
            print('Неизвестная ошибка. Код ответа: {status_code}')

    # Сохраняем список описаний
    df_all_descriptions = pd.DataFrame(all_descriptions, columns=["Description"])

    # Выгрузка в CSV
    df_all_descriptions.to_csv(file_descriptions, index=False, encoding="utf-8")

    # Сохраняем список ключевых навыков
    df_ML_key_skills = pd.DataFrame(ML_key_skills, columns=["Key skills"])

    df_ML_key_skills.to_csv(ML_key_skills_file, index=False, encoding="utf-8")

    # Сохраняем список плохих описаний для анализа
    bad_descriptionts = pd.DataFrame(bad_descriptionts, columns=["Bad description"])

    bad_descriptionts.to_csv(bad_descriptions_file, index=False, encoding="utf-8")

    return  ML_key_skills    


# description_text = """
# <p><strong>Проект - спортивная линия сайта компании. Работа в команде backend-разработки.</strong></p> <p><strong>ЧЕМ ПРЕДСТОИТ ЗАНИМАТЬСЯ:</strong></p> <ul> <li>Решать задачи, связанные с интеграциями: развивать текущие, подключать новые;</li> <li>Контролировать процесс разработки продукта на всех этапах;</li> <li>Участвовать в планировании, поддержке и координации развития текущих и новых проектов;</li> <li>Управление распределенной командой разработчиков;</li> <li>Готовить отчетность по проектам;</li> <li>Собирать базу знаний и вести проектную документацию.</li> </ul> <p><strong>ЧТО МЫ ХОТИМ ВИДЕТЬ:</strong></p> <ul> <li>Опыт работы проектным менеджером в IT от 3 лет;</li> <li>Технический бэкграунд — нам важно, чтобы ты мог разговаривать с разработчиками на одном языке;</li> <li>Понимание всего жизненного цикла разработки продукта;</li> <li>Практический опыт применения принципов Agile и использования методологий Scrum, Kanban;</li> <li>Английский язык не ниже B1.</li> </ul>
# <p>Присоединяйтесь к команде и создавайте продукты и сервисы нового поколения, которыми будут пользоваться миллионы клиентов.<br />Исследуйте, анализируйте и проектируйте бизнес-процессы. Станьте нашим мозговым центром – каждый проект будет опираться на вашу экспертизу. Вас ждут разработка, управление, совершенствование процессов и анализ требований пользователей. А значит много командной работы как внутри группы, так и с заказчиками.</p> <p><strong>Обязанности:</strong></p> <ul> <li>анализ и моделирование целевых бизнес-процессов, формирование и согласование бизнес-требований;</li> <li>сопровождение задач на этапах системного анализа, разработки и тестирования;</li> <li>формирование руководств пользователя;</li> <li>использование нотаций BPMN;</li> <li>проведение клиентских исследований;</li> <li>знания и опыт разработки требований для расчетных продуктов и платежных сервисов для юридических лиц желательно.</li> </ul> <p><strong>Требования:</strong></p> <ul> <li>знания и опыт разработки требований для процессов Расчетно-Кассового Обслуживания для юридических лиц желательно;</li> <li>опыт анализа и описания бизнес-процессов As Is и построения процессов To Be, написания клиентского пути;</li> <li>навыки сбора требований и написания бизнес-требований для разработки и модификации информационных систем;</li> <li>опыт работы по методологии agile.</li> </ul> <p> </p>
# <p>Наша компания продает на маркетплейсах, а также занимается оцифровкой для компаний, которые продают на маркетплейсах.</p> <p> </p> <p>Система оцифровки построена на базе google таблиц (google sheets)</p> <p> </p> <p>На нашей системе оцифровки, подключено уже более 400 компаний. И в связи с активным ростом компании, мы ищем человека, который усилит нашу команду.</p> <p> </p> <p>В работе есть две основных части функционала:</p> <p>1) доработки нашей системы оцифровки (только на стороне гугл таблиц, поэтому основное это уметь разрабатывать на google apps script)</p> <p> </p> <p>2) помощь и техподдержка текущих клиентов</p> <p> </p> <p> </p> <p> </p> <p>Обязанности:</p> <p> </p> <p>- Техподдержка действующих клиентов .</p> <p> </p> <p>- Индивидуальные доработки для текущих клиентов.</p> <p> </p> <p>- На основе обратной связи доработка существующих дашбордов и разработка новых.</p> <p> </p> <p>- Создание минимальной визуальной аналитики на базе того же Yandex Data Lens</p> <p> </p> <p>- разработка новых специализированных шаблонов: финансовая аналитика, рекламная и конверсионная.</p> <p> </p> <p>- Переработка текущих шаблонов</p> <p> </p> <p> </p> <p>Требования:</p> <p>- Знание Google apps Script</p> <p>- умение работать с google sheets</p> <p>- опыт финансового или статанализа, приветствуется.</p> <p> </p> <p> </p> <p>Условия:</p> <p>Полностью удаленная работа. График 5/2, иногда в экстренных случаях требуется техподдержка клиентов в выходные (до 30 минут в день)</p>
# <p>Присоединяйтесь к команде и создавайте продукты и сервисы нового поколения, которыми будут пользоваться миллионы клиентов.<br />Исследуйте, анализируйте и проектируйте бизнес-процессы. Станьте нашим мозговым центром – каждый проект будет опираться на вашу экспертизу. Вас ждут разработка, управление, совершенствование процессов и анализ требований пользователей. А значит много командной работы как внутри группы, так и с заказчиками.</p> <p><strong>Обязанности:</strong></p> <p> </p> <ul> <li>формирование бизнес-требований к изменению процессов и систем;</li> <li>сбор информации, анализ рынка и конкурентов, анализ и моделирование целевых бизнес-процессов;</li> <li>разработка и написание бизнес-кейсов, клиентских историй, бизнес-требований, руководств пользователя, предложения по внесению изменений в текущие ВНД (продукты для специальных счетов юридических лиц);</li> <li>обеспечение процесса согласования требований;</li> <li>сопровождение задач на этапах системного анализа, разработки и тестирования;</li> <li>аналитика и актуализация текущих процессов формирования коммуникаций с клиентами Среднего и Малого бизнеса на всех этапах взаимодействия с банком;</li> <li>подготовка презентаций для руководства, заказчиков, клиентов</li> <li>контроль выполнения и сроков поставленных задач.</li> </ul> <p><strong>Требования:</strong></p> <p> </p> <ul> <li>высшее образование в области финансов;</li> <li>опыт работы в роли бизнес аналитика от 1 года;</li> <li>опыт работы в кредитной организации от 3 лет;</li> <li>знание бизнес-процессов в финансовых компаниях;</li> <li>знания и опыт разработки требований для процессов Расчетно-Кассового Обслуживания для юридических лиц (знания специальных счетов 44-ФЗ, саморегулируемых организаций, платежных агентов/поставщиков приветствуются);</li> <li>навыки анализа и описания бизнес-процессов As Is и построения процессов To Be;</li> <li>навыки сбора требований и написания бизнес-требований для разработки и модификации информационных систем;</li> <li>навыки формирования схем бизнес-процессов в нотации BPMN;</li> <li>уверенное владение Power Point и MS Excel.</li> </ul> <p> </p>
# <p>В дружную команду Центра управления ИТ-процессами и качеством ищем бизнес-аналитика для разработки новых, аудита и оптимизации текущих ИТ-процессов.</p> <p><strong>Задачи:</strong></p> <ul> <li>Разработка новых, аудит и оптимизация текущих ИТ-процессов, включая моделирование в нотации BPMN 2.0;</li> <li>Разработка нормативной документации по ИТ-процессам (политики, стандарты, регламенты, методики и пр.);</li> <li>Участие в построении Каталога услуг/запросов, сервисно-ресурсных и сервисно-финансовых моделей;</li> <li>Участие в регулярной оценке зрелости/возможностей ИТ-процессов;</li> <li>Анализ запросов на доработку системы на целесообразность и соответствие стратегическим ИТ-целям;</li> <li>Участие в проектах автоматизации ИТ-процессов, включая сбор, анализ, формирование и согласование функциональных требований;</li> <li>Разработка обучающих материалов, обучение участников ИТ-процессов;</li> <li>Проведение обучения по ИТ-процессам и их автоматизации.</li> </ul> <p><strong>Мы ожадаем:</strong></p> <ul> <li>Понимание принципов процессного управления (обязательно);</li> <li>Знание хотя бы одной из нотаций: IDEF0, BPMN, EPC, Archimate, C4 (обязательно);</li> <li>Знакомство хотя бы с одним из фреймворков: ITIL, COBIT, IT4IT (желательно).</li> </ul> <p><strong>У нас твои идеи не потеряются: предлагай и обсуждай, ищи новые решения и экспериментируй. Мы всегда поддержим тебя, а ещё предложим:</strong></p> <ul> <li>достойную заработную плату;</li> <li>современный и уютный офис в 2-х минутах от м. Технопарк - для московских сотрудников;</li> <li>ДМС со стоматологией с первого месяца работы;</li> <li>скидки и бонусы на продукты и услуги от МТС, МТС Банка и партнёров;</li> <li>отсутствие дресс-кода;</li> <li>корпоративный спорт: йога, беговой клуб, вело-сообщество и другие;</li> <li>тренажерный зал в офисе;</li> <li>специальный тариф на мобильную связь;</li> <li>доступ к корпоративной библиотеке;</li> <li>регулярные образовательные курсы и тренинги от корпоративного университета;</li> <li>цифровое пространство (безбумажный прием на работу, коворкинг, электронный документооборот);</li> <li>кафе «Мечта» с полезными завтраками и вкусными обедами;</li> <li>детские дни и подарки;</li> <li>программу материальной помощи в различных жизненных ситуациях;</li> <li>социальные проекты (раздельный сбор мусора, фандоматы, благотворительные ярмарки и волонтерские акции).</li> </ul>
# <strong>Обязанности:</strong> <ul> <li>Проектировать новые и оптимизировать существующие бизнес процессы для продукта Личный кабинет сотрудника, создавая решения, которые повышают удобство и эффективность для пользователя</li> <li>Декомпозировать эпики до уровня пользовательских историй, обеспечивать их понятность для команды</li> <li>Оценивать и предлагать варианты реализации эпиков: выявлять ограничения, зависимости, сроки и сложность</li> <li>Управлять артефактами по задачам и согласовывать их с экспертами, заказчиками и смежными подразделениями</li> <li>Лидировать командную проработку бэклога и поддерживать PO при планировании и составлении дорожной карты на квартал</li> <li>Сопровождать задачи на всех этапах жизненного цикла, участвовать в приемке и обзорах работы команды.</li> </ul> <strong>Требования:</strong> <ul> <li>Высшее образование в области ИТ, экономики, менеджмента или аналогичной</li> <li>Опыт работы бизнес-аналитиком от 4-х лет</li> <li>Умение работать с бэклогом, декомпозировать задачи и организовывать груминги</li> <li>Знание Jira, Confluence и нотации BPMN для моделирования процессов</li> <li>Развитые навыки коммуникации для эффективного взаимодействия с различными подразделениями и экспертами</li> <li>Понимание технологических и бизнес-процессов, опыт выявления системных зависимостей</li> <li>Аналитическое мышление; CJM; Journey map; Figma</li> <li>Базовые навыки работы в Figma будут плюсом.</li> </ul>
# <p>Наши бренды:</p> <ul> <li> <p>Островок — для самостоятельных путешественников.</p> </li> <li> <p>B2B.Ostrovok — для тревел-агентов.</p> </li> <li> <p>Ostrovok.ru Командировки — для корпоративных клиентов.</p> </li> </ul> <p>Мы ищем <strong>Machine Learning Engineer</strong>, который займется совершенствованием наших алгоритмов ценообразования, обеспечивая прибыльность и эффективность в различных направлениях бизнеса.</p> <p><strong>Основные задачи на позиции:</strong></p> <ul> <li>Совершенствование существующей модели повышения цен и разработка новых алгоритмов динамического ценообразования, обеспечивая их масштабируемость, скорость и эффективность.</li> <li>Разработка и реализация стратегии динамического прайсинга для B2C &amp; B2A продуктов;</li> <li>Кросс-командные запуски проектов с маркетингом и бизнес-аналитикой;</li> <li>Управление полным жизненным циклом проектов машинного обучения, от генерации идеи до внедрения в производство, что на прямую влияет на опыт пользователей и финансовые показатели.</li> <li>Создание надежных конвейеров машинного обучения в режиме реального времени при поддержке инженеров, отвечающих за основной механизм бронирования отелей.</li> </ul> <p><strong>Для этого тебе понадобится:</strong></p> <ul> <li>Не менее 2х лет опыта работы в области Data Science.</li> <li>Опыт работы с одним из этих направлений - системами динамического ценообразования (ctr, uplift) или любыми видами промо, влияющими на цены (промо, промокоды, программы лояльности и т. д.).</li> <li>Уверенное знание Python и SQL.</li> <li>Опыт работы с классическими алгоритмами ML и хорошее понимание Deep Learning.</li> <li>Понимание цикла создания модели машинного обучения.</li> <li>Способность вести собственные проекты, работать как в одиночку, так и в команде.</li> <li>Английский язык от В2.</li> </ul> <p> </p>
# <p>Summary of position</p> <p>As a Business Development Manager, your primary responsibility is to drive B2B sales within the igaming industry while maintaining relationships with existing clients and partners</p> <p>Key responsibilities</p> <ul> <li> <p>Lead generation through diverse channels including active participation in industry events and exhibitions</p> </li> <li> <p>Conduct negotiations with prospective clients</p> </li> <li> <p>Define &amp; negotiate commercial terms with partners</p> </li> <li> <p>Facilitate agreement and signing of documents with partners</p> </li> <li> <p>Provide top-tier support to current B2B clients and partners</p> </li> <li> <p>Act as a client representative for internal stakeholders</p> </li> </ul> <p>Required hard skills</p> <ul> <li> <p>Proven experience in B2B sales including remote sales</p> </li> <li> <p>General understanding of the igaming market</p> </li> <li> <p>Understanding of the sales process and dynamics</p> </li> <li> <p>Proficiency in office applications like MS Excel, MS Power Point, Google Suite</p> </li> <li> <p>Fluency in English at B2 or higher level</p> </li> <li> <p>Native or bilingual proficiency in Russian</p> </li> </ul> <p>Required soft skills</p> <ul> <li> <p>Strong interpersonal skills</p> </li> <li> <p>Client-centric approach, ensuring prompt responses</p> </li> <li> <p>Results-driven mindset combined with strategic thinking</p> </li> <li> <p>Self-motivated and proactive</p> </li> <li> <p>Data driven decision making</p> </li> <li> <p>Passion for sports</p> </li> </ul>
# <p><strong>Мы предлагаем:</strong></p> <ul> <li>Работу в крупнейшей транспортно-логистической компании в России</li> <li>Возможность стать экспертом в своем направлении, пройти обучение и сделать карьеру</li> <li>Официальное оформление, социальный пакет</li> <li>Премию по результатам работы</li> <li>ДМС, включая стоматологию</li> <li>График работы 5/2</li> </ul> <p><strong>Основные задачи:</strong></p> <ul> <li>Финансовое и операционное моделирование</li> <li>Оценка бизнеса и анализ финансовой отчётности компаний</li> <li>Анализ ключевых операционных показателей эффективности работы направления логистики с формированием аналитических записок</li> <li>Текущий мониторинг исполнения бюджета</li> <li>Участие в бюджетном процессе компании</li> <li>План-фактный анализ отчётности с анализом чувствительности и составление аналитической записки по результатам отчётного периода</li> <li>Подготовка бизнес-моделей для новых продуктов и проектов</li> <li>Оценка экономической целесообразности запуска проектов; инвестиционный анализ; структурирование данных (Excel, PowerQuery)</li> <li>Подготовка визуальных представлений показателей (дашборды с KPIs), сегментация и вывод различных данных для их оценки и принятия управленческих решений</li> <li>Участие в процессе автоматизации операционных и управленческих отчетов</li> </ul> <p><strong>Мы ожидаем:</strong></p> <ul> <li>Опыт работы от трёх лет на позиции экономиста/инвестиционного аналитика/бизнес-аналитика</li> <li>Знание основ управленческого учёта, бюджетирования</li> <li>Опыт работы в логистической компании будет преимуществом</li> </ul>
# """

def get_terms_from_description(description, bad_descriptions):

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
        bad_descriptions.append(description)
        return []
    
    # Шаг 3: Очистка текста от html тегов
    cleaned_items = [re.sub(r"<.*?>", "", item).strip() for item in raw_list_items]

    # Шаг 4: Поиск терминов
    terms = []
    for line in cleaned_items:
        terms += re.findall(r"\b(?:[A-Za-z0-9]*[A-Za-z]+[A-Za-z0-9]*)(?:[-\s][A-Za-z0-9]*[A-Za-z]+[A-Za-z0-9]*)*\b", line)

    return list(set(terms))


def get_hh_analytics(query_string='ML',role='developer',areas=['1']):
    """
    возвращает 10 самых популярных требований и сводку по з/п
    """

    # парсим список вакансий из поиска по запросу
    vacancies = get_vacancies_by_query(search_query=query_string, area=areas, per_page=100)
    # vacancies = load_vacancies_from_json()
    num_vacancies = len(vacancies)
    print('Найдено вакансиЙ:', num_vacancies)
    
    # Извлекаем ключевые навыки из полного описания вакансий
    ML_key_skills = get_terms_from_vacancies(vacancies)
    # df_ML_key_skills = pd.read_csv(ML_key_skills_file)

    print(ML_key_skills[:20])

    # Частотный анализ
    term_counts = Counter(term.lower() for term in ML_key_skills)

    # Получение топ-20 терминов
    top_terms = term_counts.most_common(20)

    # Печать результата
    for term, count in top_terms:
        print(f"{term}: {count}")

    # Преобразование в DataFrame
    df = pd.DataFrame(term_counts.items(), columns=['Требования', 'Количество'])

    # Добавление колонки 'Процент'
    df['Процент'] = (df['Количество'] / num_vacancies) * 100

    # Округление до двух десятичных знаков
    df['Процент'] = df['Процент'].round(1)

    print("\nDataFrame с колонкой 'Процент':")
    print(df)

    # Сортировка по количеству
    df = df.sort_values(by='Количество', ascending=False)

    # Сохранение в CSV
    df.to_csv(ML_key_skills_file, index=False)

    print(f"Данные успешно сохранены в файл {ML_key_skills_file}.")

    # Получаем сводку по з/п

    average_salary_by_role = get_salary_analytics(vacancies)

    return df['Требования'].head(10).tolist(), average_salary_by_role


def main():
    get_hh_analytics()

if __name__ == "__main__":
    main()
