import os
import sqlite3
from security import encrypt_password, decrypt_password

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
    return False

def add_service_to_db(service, login, encrypted_password):
    try:
        connection = sqlite3.connect(db_file)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO hasla (serwis, login, haslo) VALUES (?, ?, ?)", (service, login, encrypted_password))
        connection.commit()
        connection.close()
    except sqlite3.Error as e:
        raise Exception(f"Błąd bazy danych: {e}")

def update_service_in_db(service_id, service, login, encrypted_password):
    try:
        connection = sqlite3.connect(db_file)
        cursor = connection.cursor()
        cursor.execute("UPDATE hasla SET serwis = ?, login = ?, haslo = ? WHERE id = ?", 
                       (service, login, encrypted_password, service_id))
        connection.commit()
        connection.close()
    except sqlite3.Error as e:
        raise Exception(f"Błąd bazy danych: {e}")

def delete_service_from_db(service_id):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM hasla WHERE id = ?", (service_id,))
    connection.commit()
    connection.close()

def get_password_by_id(service_id):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("SELECT haslo FROM hasla WHERE id = ?", (service_id,))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else None

def fetch_all_passwords():
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("SELECT id, serwis, login, haslo FROM hasla")
    rows = cursor.fetchall()
    connection.close()
    return rows

def import_passwords_from_csv(file_path):
    import csv
    from security import encrypt_password

    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            serwis = row.get("Serwis", "").strip()
            login = row.get("Login", "").strip()
            haslo = row.get("Hasło", "").strip()
            if serwis and login and haslo:
                zaszyfrowane = encrypt_password(haslo)
                add_service_to_db(serwis, login, zaszyfrowane)

def export_passwords_to_csv(file_path):
    import csv
    from security import decrypt_password

    passwords = fetch_all_passwords()
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Serwis", "Login", "Hasło"])
        for row in passwords:
            _, serwis, login, zaszyfrowane = row
            odszyfrowane = decrypt_password(zaszyfrowane)
            writer.writerow([serwis, login, odszyfrowane])
