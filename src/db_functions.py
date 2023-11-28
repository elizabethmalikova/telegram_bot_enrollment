import sqlite3
from helper import log_day


# Функция для создания таблицы в базе данных, если её нет
def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS enrollments
                      (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, user_real_name TEXT, enable BOOLEAN)''')
    conn.commit()


# Функция для добавления записи в базу данных
def add_enrollment(conn, user_id, username, first_name, enable = True):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO enrollments (user_id, username, first_name, user_real_name, enable) VALUES (?, ?, ?, ?, ?)",
                   (user_id, username, first_name, 'NONE', enable))
    conn.commit()


# Функция для получения массива никнеймов записанных пользователей
def get_enrollments(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM enrollments")
    rows = cursor.fetchall()
    return [row[0] for row in rows]


# Функция для проверки, записан ли пользователь
def is_enrolled(conn, user_id):
    print(log_day(), "Проверка записан ли юзер и включена ли у него запись...")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, user_real_name, enable FROM enrollments WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row is not None:
        user_exists = True
        if row[2] == 1:
            enable_status = True
        else:
            enable_status = False
        if row[1] == 'NONE':
            real_name_exist = False
        else:
            real_name_exist = True
    else:
        user_exists = False
        enable_status = False
        real_name_exist = False

    return user_exists, enable_status, real_name_exist


# очистка таблицы
def delete_table(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enrollments")
    conn.commit()
    conn.close()


# проверка существования таблицы
def table_exists(conn):
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", ('enrollments.db',))
    return cursor.fetchone() is not None


def enable_enrollment(conn, user_id):
    print(log_day(), "Включение записи для юзера...")
    cursor = conn.cursor()
    cursor.execute("UPDATE enrollments SET enable = ? WHERE user_id = ?", (True, user_id))
    conn.commit()


def disable_enrollment(conn, user_id):
    print(log_day(), "Выключение записи для юзера...")
    cursor = conn.cursor()
    cursor.execute("UPDATE enrollments SET enable = ? WHERE user_id = ?", (False, user_id))
    conn.commit()


# формирование списка
def get_random_usernames_with_names(conn, count_users):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, user_real_name FROM enrollments WHERE enable = 1 ORDER BY RANDOM() LIMIT ?",
                   (count_users,))
    rows = cursor.fetchall()
    return rows


def clear_enable(conn):
    print(log_day(), 'очищаю все записи')
    cursor = conn.cursor()
    cursor.execute("UPDATE enrollments SET enable = ?", (0,))
    conn.commit()
    conn.close()


def count_total_enrollments(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM enrollments WHERE enable = 1")
    total_enrollments = cursor.fetchone()[0]
    return total_enrollments


def say_name(conn, user_id, user_real_name):
    print(log_day(), 'записываю имя и фамилию пользователя')
    cursor = conn.cursor()
    cursor.execute('''
            UPDATE enrollments SET user_real_name = ? WHERE user_id = ?
        ''', (user_real_name, user_id))
    conn.commit()
