import psycopg2

from src.config import config


class DBManager:
    """Класс для взаимодействия с базой данных"""

    def __init__(self, db_name: str, params_db: dict):
        self.avg_salary = None
        self.params_db = params_db
        self.db_name = db_name

    def get_companies_and_vacancies_count(self):
        """Метод считает количество вакансий по каждой компании"""
        with psycopg2.connect(**self.params_db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT company_name, COUNT(vacancy.company_id)
                    FROM company
                    INNER JOIN vacancy ON company.company_id=vacancy.company_id
                    GROUP BY company_name
                    """
                )
                result = cur.fetchall()
        return result

    def get_all_vacancies(self):
        """Метод выводит список вакансий со всеми данными"""
        with psycopg2.connect(**self.params_db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT company_name, vacancy_name, salary_from, salary_to, salary_currency, url
                    FROM company
                    RIGHT JOIN vacancy USING(company_id)
                    """
                )
                result = cur.fetchall()
        return result

    def get_avg_salary(self):
        """Метод получает среднюю зарплату по всем вакансиям"""
        with psycopg2.connect(**self.params_db) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT AVG(salary_from) FROM vacancy")
                result = cur.fetchone()
                avg_salary_value = result[0] if result and result[0] is not None else 0
                self.avg_salary = float(avg_salary_value)
        return f"Средняя зарплата по всем вакансиям - {self.avg_salary} руб."

    def get_vacancies_with_higher_salary(self):
        """Метод получает список вакансий, у которых зарплата выше средней зарплаты"""
        with psycopg2.connect(**self.params_db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM vacancy
                    WHERE salary_to >= (SELECT AVG(salary_to) FROM vacancy)
                    """
                )
                result = cur.fetchall()
        return result

    def get_vacancies_with_keyword(self, keyword):
        """Метод получает список вакансий по ключевому слову в названии"""
        # Можно оставить как есть или привести к нижнему регистру для поиска
        keyword_lower = keyword.lower()
        with psycopg2.connect(**self.params_db) as conn:
            with conn.cursor() as cur:
                query = "SELECT * FROM vacancy WHERE LOWER(vacancy_name) ILIKE %s"
                cur.execute(query, ("%" + keyword_lower + "%",))
                result = cur.fetchall()
        return result


if __name__ == "__main__":
    params = config("../database.ini")
    test = DBManager("company", params)
    print(test.get_companies_and_vacancies_count())
    print(test.get_all_vacancies())
    print(test.get_avg_salary())
    print(test.get_vacancies_with_higher_salary())
    print(test.get_vacancies_with_keyword("стажёр"))
