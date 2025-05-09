import sqlite3
import os

db_file = './baza_hasel.db'

def create_database_if_not_exists():
    if not os.path.exists(db_file):
        connection = sqlite3.connect(db_file)
        cursor = connection.cursor()
        cursor.execute('''CREATE TABLE hasla (
                            id INTEGER PRIMARY KEY,
                            serwis TEXT NOT NULL,
                            login TEXT NOT NULL,
                            haslo TEXT NOT NULL
                        )''')
        connection.commit()
        connection.close()
        return True
    else:
        return False

def get_all_services():
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("SELECT id, serwis FROM hasla")
    rows = cursor.fetchall()
    connection.close()
    return rows

def add_service(service, login, password):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO hasla (serwis, login, haslo) VALUES (?, ?, ?)", (service, login, password))
    connection.commit()
    connection.close()

def get_service(service_id):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("SELECT serwis, login, haslo FROM hasla WHERE id = ?", (service_id,))
    row = cursor.fetchone()
    connection.close()
    return row

def update_service(service_id, service, login, password):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("UPDATE hasla SET serwis = ?, login = ?, haslo = ? WHERE id = ?", (service, login, password, service_id))
    connection.commit()
    connection.close()
