import os
import glob
import platform
import json
import sqlite3
import pandas as pd
from tabulate import tabulate

def get_data_folder():
    if platform.system() == "Windows":
        return os.path.join(os.environ["APPDATA"], "PasswordManager")
    elif platform.system() == "Darwin":
        return os.path.expanduser("~/Library/Application Support/PasswordManager")
    else:
        return os.path.expanduser("~/.config/PasswordManager")

def find_files_with_prefix(folder, prefix):
    pattern = os.path.join(folder, f"{prefix}*")
    return glob.glob(pattern)

def test_file_and_preview(filepath, filetype):
    _, ext = os.path.splitext(filepath)

    if ext.lower() == ".enc":
        return "Plik zaszyfrowany", ""

    try:
        if filetype == "config":
            with open(filepath, "r") as f:
                data = json.load(f)
            pin = data.get("pin", None)
            if pin is not None:
                return "Odczytano PIN", f"PIN: {pin}"
            else:
                return "Brak pola 'pin'", ""
        
        elif filetype == "db":
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hasla'")
            if not cursor.fetchone():
                return "Brak tabeli 'hasla'", ""
            cursor.execute("SELECT * FROM hasla LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                return "Odczytano dane z bazy", f"{row[1]} / {row[2]}"
            else:
                return "Brak rekordów w tabeli", ""
    except json.JSONDecodeError:
        return "Niepoprawny format JSON", ""
    except sqlite3.DatabaseError:
        return "Plik nie jest prawidłową bazą SQLite", ""
    except Exception as e:
        return f"Błąd: {type(e).__name__}", str(e).splitlines()[0]

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folders = {
        "no protect": os.path.join(script_dir, "lite"),
        "protected": get_data_folder()
    }

    results = []

    for label, folder in folders.items():
        for prefix, ftype in [("baza_hasel", "db"), ("config", "config")]:
            files = find_files_with_prefix(folder, prefix)
            for file in files:
                status, preview = test_file_and_preview(file, ftype)
                results.append({
                    "Folder": label,
                    "Plik": os.path.basename(file),
                    "Typ": ftype,
                    "Status": status,
                    "Podgląd": preview
                })

    print(tabulate(results, headers="keys", tablefmt="grid"))

    df = pd.DataFrame(results)
    df.to_excel("wyniki.xlsx", index=False)
    print("\nDane zapisane do pliku Excel: wyniki.xlsx")

if __name__ == "__main__":
    main()
