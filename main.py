from src.config import config
from src.database_connect import db_create, db_create_table, load_to_database_company
from src.dbmanager import DBManager


def main():
    # Создание базы данных и таблиц
    config_path = "database.ini"
    db_create(config_path)
    db_create_table()
    load_to_database_company()

    params = config()

    db_company = DBManager("company", params)

    while True:
        user_enter = input(
            """\nВыберите действие:
1. Получить количество вакансий по каждой компании
2. Получить все вакансии по каждой компании
3. Получить среднюю зарплату по всем компаниям
4. Вывести вакансии с зарплатой выше средней
5. Найти вакансии по ключевому слову в названии
0. Выход\n"""
        )
        if user_enter == "0":
            break

        try:
            if user_enter == "1":
                result = db_company.get_companies_and_vacancies_count()
                for res in result:
                    print(f"{res[0]} - {res[1]} вакансий.")
            elif user_enter == "2":
                result = db_company.get_all_vacancies()
                for res in result:
                    print(
                        f"Компания: {res[0]}, "
                        f"Вакансия: {res[1]}, "
                        f"Зарплата: от {res[2]} до {res[3]} руб., "
                        f"Ссылка: {res[5]}"
                    )
            elif user_enter == "3":
                print(db_company.get_avg_salary())
            elif user_enter == "4":
                result = db_company.get_vacancies_with_higher_salary()
                for res in result:
                    print(f"{res[2]}, зарплата: от {res[3]} до {res[4]} руб., ссылка: {res[6]}, описание: {res[7]}")
            elif user_enter == "5":
                keyword = input("Введите ключевое слово:\n").lower()
                result = db_company.get_vacancies_with_keyword(keyword)
                for res in result:
                    print(f"{res[2]}, зарплата: от {res[3]} до {res[4]} руб., ссылка: {res[6]}, описание: {res[7]}")
            else:
                print("Некорректный ввод, попробуйте снова.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    main()
