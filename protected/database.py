import os
import sqlite3
import csv
from security import encrypt_password, decrypt_password, generate_keys
from paths import get_local_path
from security_files import decrypt_files
db_file = get_local_path("baza_hasel.db.enc")

# db.py – dodaj na końcu
_active_connection = None  # zmienna globalna

def get_connection():
    global _active_connection
    if _active_connection is None:
        _active_connection = sqlite3.connect(db_file)
    return _active_connection

def close_connection():
    global _active_connection
    if _active_connection:
        _active_connection.close()
        _active_connection = None

def add_service_to_db(service, login, password_plaintext):
    try:
        encrypted_password = encrypt_password(password_plaintext)
        with sqlite3.connect(db_file) as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO hasla (serwis, login, haslo) VALUES (?, ?, ?)",
                           (service, login, encrypted_password))
            connection.commit()
    except sqlite3.Error as e:
        raise Exception(f"Błąd bazy danych przy dodawaniu: {e}")

def create_database_if_not_exists():
    if not os.path.exists(db_file):
        generate_keys()  # Generowanie klucza szyfrowania
        with sqlite3.connect(db_file) as connection:
            cursor = connection.cursor()
            cursor.execute('''CREATE TABLE hasla (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                serwis TEXT NOT NULL,
                                login TEXT NOT NULL,
                                haslo TEXT NOT NULL
                            )''')
            
            # Dodajemy przykładowe dane
            demo_password = encrypt_password("haslo123")
            cursor.execute("INSERT INTO hasla (serwis, login, haslo) VALUES (?, ?, ?)",
                           ("example.com", "demo@example.com", demo_password))
            connection.commit()
        close_connection()  # Zamykamy połączenie
        return True
    return False
    


def update_service_in_db(service_id, service, login, password_plaintext):
    try:
        encrypted_password = encrypt_password(password_plaintext)
        with sqlite3.connect(db_file) as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE hasla SET serwis = ?, login = ?, haslo = ? WHERE id = ?",
                           (service, login, encrypted_password, service_id))
            connection.commit()
    except sqlite3.Error as e:
        raise Exception(f"Błąd bazy danych przy aktualizacji: {e}")

def delete_service_from_db(service_id):
    try:
        with sqlite3.connect(db_file) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM hasla WHERE id = ?", (service_id,))
            connection.commit()
    except sqlite3.Error as e:
        raise Exception(f"Błąd bazy danych przy usuwaniu: {e}")

def get_password_by_id(service_id) -> str:
    try:
        with sqlite3.connect(db_file) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT haslo FROM hasla WHERE id = ?", (service_id,))
            result = cursor.fetchone()
            return decrypt_password(result[0]) if result else None
    except Exception as e:
        raise Exception(f"Błąd przy odczycie hasła: {e}")

def fetch_all_passwords():
    try:
        with sqlite3.connect(db_file) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id, serwis, login, haslo FROM hasla")
            return cursor.fetchall()
    except sqlite3.Error as e:
        raise Exception(f"Błąd bazy danych przy pobieraniu haseł: {e}")

def import_passwords_from_csv(file_path):
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                serwis = row.get("Serwis", "").strip()
                login = row.get("Login", "").strip()
                haslo = row.get("Hasło", "").strip()
                if serwis and login and haslo:
                    add_service_to_db(serwis, login, haslo)
    except Exception as e:
        raise Exception(f"Błąd przy imporcie CSV: {e}")

def export_passwords_to_csv(file_path):
    try:
        data = fetch_all_passwords()
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["Serwis", "Login", "Hasło"])
            writer.writeheader()
            for row in data:
                _, service, login, encrypted = row
                decrypted = decrypt_password(encrypted)
                writer.writerow({
                    "Serwis": service,
                    "Login": login,
                    "Hasło": decrypted
                })
    except Exception as e:
        raise Exception(f"Błąd przy eksporcie CSV: {e}")



def force_sqlite_write_if_empty():
    db_path = get_local_path("baza_hasel.db")
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hasla")
            count = cursor.fetchone()[0]
            if count == 0:
                print("[SQLITE] Dodaję tymczasowy rekord, by wymusić zapis...")
                cursor.execute("INSERT INTO hasla (serwis, login, haslo) VALUES (?, ?, ?)", 
                               ('__temp__', '__temp__', '__temp__'))
                conn.commit()
                cursor.execute("DELETE FROM hasla WHERE serwis = ?", ('__temp__',))
                conn.commit()
                print("[SQLITE] Tymczasowy rekord usunięty.")
    except Exception as e:
        print(f"[force_sqlite_write_if_empty] Błąd: {e}")
