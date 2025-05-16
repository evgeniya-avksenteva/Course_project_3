import psycopg2

from src.config import config
from src.hh_load_vacancies import HeadHunterAPI


def db_create(config_path):
    """Создает базу данных 'company', предварительно завершая все соединения."""
    sys_params = config(config_path, section="postgresql")
    # Подключаемся к базе postgres, чтобы иметь возможность управлять базами
    params_for_postgres = sys_params.copy()
    params_for_postgres["dbname"] = "postgres"
    conn = psycopg2.connect(**params_for_postgres)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            # Завершаем все активные соединения с базой 'company'
            cur.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'company' AND pid <> pg_backend_pid();
            """
            )
            # Удаляем базу, если она существует
            cur.execute("DROP DATABASE IF EXISTS company;")
            # Создаем новую базу
            cur.execute("CREATE DATABASE company;")
    finally:
        conn.close()


def db_create_table(config_path: str = "database.ini") -> None:
    """Создает таблицы в базе данных."""
    params = config(config_path)
    conn = psycopg2.connect(**params)
    try:
        with conn.cursor() as cur:
            # Создаем таблицу company
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS company (
                    id SERIAL UNIQUE,
                    company_id INT PRIMARY KEY,
                    company_name VARCHAR(255) NOT NULL
                );
            """
            )
            # Создаем таблицу vacancy
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS vacancy (
                    vacancy_id SERIAL PRIMARY KEY,
                    company_id INT REFERENCES company(company_id),
                    vacancy_name VARCHAR(255) NOT NULL,
                    salary_from INT DEFAULT 0,
                    salary_to INT DEFAULT 0,
                    salary_currency VARCHAR(50),
                    url VARCHAR(255),
                    description TEXT
                );
            """
            )
        conn.commit()
    finally:
        conn.close()


def load_to_database_company(config_path: str = "database.ini") -> None:
    """Загружает данные о вакансиях из API в базу данных."""
    params = config(config_path)
    conn = psycopg2.connect(**params)
    try:
        hh = HeadHunterAPI()
        hh_employers = hh.load_vacancies()  # список компаний (id и name)
        hh_vacancy = hh.correct_vacancy(10)  # список вакансий

        with conn.cursor() as cur:
            for employer in hh_employers:
                # Вставляем компанию, избегая дублирования (если нужно)
                cur.execute(
                    """
                    INSERT INTO company (company_id, company_name)
                    VALUES (%s, %s)
                    ON CONFLICT (company_id) DO NOTHING
                    RETURNING company_id;
                """,
                    (employer["id"], employer["name"]),
                )

                result = cur.fetchone()
                if result:
                    company_id_db = result[0]
                else:
                    # Если компания уже есть, получаем ее id
                    cur.execute("SELECT company_id FROM company WHERE company_id=%s;", (employer["id"],))
                    company_id_db = cur.fetchone()[0]

                for vacancy in hh_vacancy:
                    if int(vacancy["employer"]["id"]) == int(employer["id"]):
                        salary_info = vacancy.get("salary") or {}
                        salary_from = salary_info.get("from") or 0
                        salary_to = salary_info.get("to") or 0
                        salary_currency = salary_info.get("currency") or ""
                        description = vacancy.get("snippet", {}).get("responsibility") or ""

                        cur.execute(
                            """
                            INSERT INTO vacancy (
                                company_id, vacancy_name, salary_from, salary_to,
                                salary_currency, url, description
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s);
                        """,
                            (
                                company_id_db,
                                vacancy["name"],
                                salary_from,
                                salary_to,
                                salary_currency,
                                vacancy["url"],
                                description,
                            ),
                        )
    finally:
        conn.commit()
        conn.close()


if __name__ == "__main__":
    db_create("../database.ini")  # Создает базу данных 'company'
    db_create_table("../database.ini")  # Создает таблицы
    load_to_database_company("../database.ini")  # Загружает вакансии
