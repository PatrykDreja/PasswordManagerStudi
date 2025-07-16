import sys
import time
from PyQt5.QtWidgets import QApplication, QMessageBox, QLineEdit, QPushButton
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QCoreApplication, QTimer
from ui import PasswordManager 
import csv
import os

# Statystyki i kontrola ataku
start_time = None
end_time = None
access_granted = False
requires_2fa = False
attempts = 0
failed_2fa_attempts = 0
MAX_2FA_ATTEMPTS = 5  # maksymalna liczba błędnych prób 2FA

def auto_close_msgbox():
    global requires_2fa, failed_2fa_attempts
    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, QMessageBox) and widget.isVisible():
            msg_text = widget.text().lower()

            # Sprawdź, czy pojawiło się żądanie 2FA
            if "kod 2fa" in msg_text or "autoryzacja" in msg_text or "2fa" in msg_text:
                requires_2fa = True

            # Obsługa błędnego kodu 2FA
            if "niepoprawny kod 2fa" in msg_text or "błędny kod 2fa" in msg_text:
                failed_2fa_attempts += 1
                print(f"[DEBUG] Niepoprawny kod 2FA - próba {failed_2fa_attempts}/{MAX_2FA_ATTEMPTS}")

                if failed_2fa_attempts >= MAX_2FA_ATTEMPTS:
                    print("Przekroczono maksymalną liczbę prób 2FA. Zamykanie aplikacji...")
                    QCoreApplication.quit()
                    return


            # Kliknij OK automatycznie
            ok_button = widget.button(QMessageBox.Ok)
            if ok_button:
                QTest.mouseClick(ok_button, Qt.LeftButton)

        # Automatycznie wpisz kod 2FA w dialogu i zatwierdź
        if widget.__class__.__name__ == "TwoFactorDialog" and widget.isVisible():
            for child in widget.children():
                if isinstance(child, QLineEdit):
                    child.setText("123456")  # wpisz testowy kod 2FA
            for child in widget.children():
                if isinstance(child, QPushButton) and "ok" in child.text().lower():
                 QTest.mouseClick(child, Qt.LeftButton)

def brute_force_gui():
    global start_time, end_time, access_granted, attempts, requires_2fa, failed_2fa_attempts

    app = QApplication(sys.argv)
    window = PasswordManager()
    window.show()

    # Timer do zamykania okienek i automatycznego wpisywania kodu 2FA
    timer = QTimer()
    timer.timeout.connect(auto_close_msgbox)
    timer.start(200)

    start_time = time.time()

    for i in range(10000):
        if failed_2fa_attempts >= MAX_2FA_ATTEMPTS:
            print(f"Przerwano atak po {failed_2fa_attempts} błędnych próbach kodu 2FA.")
            break

        test_pin = f"{i:04d}"
        attempts += 1

        window.pin_input.clear()
        QTest.keyClicks(window.pin_input, test_pin)
        QTest.mouseClick(window.submit_pin_button, Qt.LeftButton)

        QCoreApplication.processEvents()
        QTest.qWait(1000)  # poczekaj na odpowiedź GUI

        if hasattr(window, "pin_entered") and window.pin_entered:
            access_granted = True
            end_time = time.time()
            print(f"Znaleziono poprawny PIN: {test_pin}")
            break

    if not access_granted:
        end_time = time.time()
        print("Nie znaleziono PIN-u")

    # Metryki
    czas_do_dostępu = round(end_time - start_time, 2)
    print("\nSTATYSTYKI")
    print(f"czas_do_dostępu: {czas_do_dostępu} sekund")
    print(f"liczba_prób: {attempts}")
    print(f"czy_dostęp_uzyskany: {access_granted}")
    print(f"czy_wymagano_2FA: {requires_2fa}")
    print(f"błędne próby 2FA: {failed_2fa_attempts}")

    # Pytanie o nazwę aplikacji (raz przy uruchomieniu)
    app_name = input("Podaj nazwę testowanej aplikacji (np. Aplikacja 1): ")

    # Ścieżka pliku CSV
    csv_file = "brute_force_wyniki.csv"

    # Sprawdź, czy plik istnieje – jeśli nie, dodaj nagłówek
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["aplikacja", "czas_do_dostępu", "liczba_prób", "czy_dostęp_uzyskany", "czy_wymagano_2FA", "błędne próby 2FA"])
        writer.writerow([
            app_name,
            czas_do_dostępu,
            attempts,
            access_granted,
            requires_2fa,
            failed_2fa_attempts
        ])

    print(f"\nWyniki zapisano do pliku: {csv_file}")

    sys.exit(app.exec_())

if __name__ == "__main__":
    brute_force_gui()