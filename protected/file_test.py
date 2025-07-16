import sqlite3
import json
import os
from paths import get_local_path
def load_pin_from_config(config_file):
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
            return config.get("pin")
    except FileNotFoundError:
        print(f"Plik {config_file} nie został znaleziony.")
        return None
    except json.JSONDecodeError:
        print(f"Błąd podczas odczytu pliku {config_file}.")
        return None


def load_data_from_db(db_file):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hasla")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Błąd połączenia z bazą danych: {e}")
        return []

def display_data(rows):
    if rows:
        for row in rows:
            print(f"Serwis: {row[1]}, Login: {row[2]}, Hasło: {row[3]}")
    else:
        print("Brak danych w bazie.")

def main():
    

    db_file = get_local_path("baza_hasel.db.enc")
    config_file = get_local_path("config.json.enc")

    
    pin = load_pin_from_config(config_file)
    
    if pin:
        print("PIN załadowany pomyślnie.")
        print(f"PIN to: {pin}")  # <- Wyświetlenie PIN-u
        
        # Wczytanie danych z bazy
        rows = load_data_from_db(db_file)
        
        if rows:
            print("Dane z bazy danych:")
            display_data(rows)
        else:
            print("Brak danych w bazie.")
    else:
        print("Nie udało się załadować PIN.")

if __name__ == "__main__":
    main()
