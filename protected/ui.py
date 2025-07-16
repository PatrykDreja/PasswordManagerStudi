import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QLabel, QMessageBox, QTreeWidget, QTreeWidgetItem, QMenu,
    QDialog, QTextEdit, QApplication, QCheckBox,
    QTableWidget, QTableWidgetItem, QHBoxLayout, QFileDialog, QHeaderView,
    QInputDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from mfa import get_qr_code_image, verify_code, get_or_create_secret
from database import fetch_all_passwords, add_service_to_db, create_database_if_not_exists
from security import encrypt_password, generate_keys, decrypt_password, save_pin, get_saved_pin 
from paths import get_local_path
from security_files import close_db_and_encrypt, encrypt_files, decrypt_files
import time
config_file = get_local_path("config.json")


class PasswordManager(QMainWindow):
    def __init__(self):
        super().__init__()
        if create_database_if_not_exists():
            self.setWindowTitle("🔐 Menedżer Haseł")
            self.setGeometry(100, 100, 1200, 700)
            self.pin_entered = False
            self.setup_ui()
        else:
            decrypt_files()
            self.setWindowTitle("🔐 Menedżer Haseł")
            self.setGeometry(100, 100, 1200, 700)
            self.pin_entered = False
            self.setup_ui()
            

    def closeEvent(self, event):

        self.password_table.setRowCount(0)
        self.loaded_passwords = []

        QApplication.processEvents()

        close_db_and_encrypt()
        event.accept()
    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.central_widget.setStyleSheet("QWidget { background-color: #ecf0f1; }")

        self.title_label = QLabel("🔐 Menedżer Haseł")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin: 20px 0;
            }
        """)
        self.layout.addWidget(self.title_label)

        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setPlaceholderText("Wprowadź PIN")
        self.pin_input.returnPressed.connect(self.check_or_set_pin)
        self.pin_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #3498db;
                border-radius: 10px;
                font-size: 16px;
                background-color: white;
            }
        """)
        self.layout.addWidget(self.pin_input)

        self.submit_pin_button = QPushButton("Potwierdź PIN")
        self.submit_pin_button.clicked.connect(self.check_or_set_pin)
        self.submit_pin_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.layout.addWidget(self.submit_pin_button)

        self.password_table = QTableWidget()
        self.password_table.setColumnCount(4)
        self.password_table.setHorizontalHeaderLabels(["Serwis", "Login", "Hasło", "Akcje"])
        self.password_table.setVisible(False)
        self.password_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                font-size: 14px;
            }
        """)
        self.layout.addWidget(self.password_table)
        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("Nazwa serwisu")
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Login / e-mail")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Hasło")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.show_password_checkbox = QCheckBox("👁️ Pokaż hasło")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        self.show_password_checkbox.setVisible(False)
        self.layout.addWidget(self.show_password_checkbox)

        for widget in (self.service_input, self.login_input, self.password_input):
            widget.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid #95a5a6;
                    border-radius: 10px;
                    font-size: 14px;
                    background-color: #ffffff;
                }
            """)
            widget.setVisible(False)
            self.layout.addWidget(widget)

        #Przycisk dodawania hasła
        self.add_password_button = QPushButton("Dodaj nowe hasło")
        self.add_password_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        self.add_password_button.clicked.connect(self.handle_add_password)
        self.add_password_button.setVisible(False)
        self.layout.addWidget(self.add_password_button)
        self.export_button = QPushButton("Eksportuj hasła")
        self.export_button.clicked.connect(self.export_passwords)
        self.export_button.setVisible(False)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #219150;
            }
        """)
        self.layout.addWidget(self.export_button)

        self.import_button = QPushButton("Importuj hasła")
        self.import_button.clicked.connect(self.import_passwords)
        self.import_button.setVisible(False)
        self.import_button.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #732d91;
            }
        """)
        self.layout.addWidget(self.import_button)

    def check_or_set_pin(self):
        entered_pin = self.pin_input.text()

        # ✅ Zabezpieczenie: nie pozwalaj na ponowną konfigurację, jeśli istnieje zaszyfrowany plik
        if not os.path.exists(config_file) and not os.path.exists(config_file + ".enc"):
            # To naprawdę pierwsze uruchomienie → ustaw PIN + MFA
            secret = get_or_create_secret()

            if secret:
                # 2FA istnieje → najpierw trzeba je potwierdzić
                dialog = TwoFactorDialog(self)
                if dialog.exec_() == QDialog.Accepted and dialog.result:
                    save_pin(entered_pin)
                    QMessageBox.information(self, "Akceptowano PIN", "Uzyskano dostęp do aplikacji.")
                    self.unlock_ui()
                else:
                    QMessageBox.critical(self, "Błąd", "Niepoprawny kod 2FA. brak dostępu do aplikacji.")
            else:
                # 2FA nie istnieje → normalna pierwsza konfiguracja
                save_pin(entered_pin)
                QMessageBox.information(self, "Ustawiono PIN", "Nowy PIN został zapisany.")

                dialog = Setup2FADialog(self)
                if dialog.exec_() == QDialog.Accepted and dialog.result:
                    QMessageBox.information(self, "Gotowe", "2FA zostało skonfigurowane.")
                    self.unlock_ui()
                else:
                    QMessageBox.critical(self, "Błąd", "Nie skonfigurowano 2FA.")
        else:
            # 🔐 Konfiguracja już istnieje – sprawdź PIN i kod 2FA
            saved_pin = get_saved_pin()
            if entered_pin == saved_pin:
                secret = get_or_create_secret()

                if secret is None:
                    dialog = Setup2FADialog(self)
                    if dialog.exec_() == QDialog.Accepted and dialog.result:
                        QMessageBox.information(self, "Gotowe", "2FA zostało skonfigurowane.")
                        self.unlock_ui()
                    else:
                        QMessageBox.critical(self, "Błąd", "Nie skonfigurowano 2FA.")
                else:
                    dialog = TwoFactorDialog(self)
                    if dialog.exec_() == QDialog.Accepted and dialog.result:
                        self.unlock_ui()
                    else:
                        QMessageBox.critical(self, "Błąd", "Niepoprawny kod 2FA.")
            else:
                QMessageBox.critical(self, "Błąd", "Niepoprawny PIN.")





    def unlock_ui(self):
        # Pokazujemy wszystko po poprawnym PINie
        self.pin_input.setDisabled(True)
        self.submit_pin_button.setDisabled(True)
        self.password_table.setVisible(True)
        self.service_input.setVisible(True)
        self.login_input.setVisible(True)
        self.password_input.setVisible(True)
        self.add_password_button.setVisible(True)
        self.pin_entered = True
        self.export_button.setVisible(True)
        self.import_button.setVisible(True)
        self.show_password_checkbox.setVisible(True)
        self.password_table.setColumnHidden(2, False)  # To jest poprawna linia
        self.load_passwords()

    def load_passwords(self):
        if not self.pin_entered:
            QMessageBox.warning(self, "Błąd", "Najpierw wprowadź poprawny PIN.")
            return

        try:
            self.password_table.setRowCount(0)
            self.loaded_passwords = fetch_all_passwords()

            for row_index, row in enumerate(self.loaded_passwords):
                id_, service, login, encrypted = row
                decrypted = decrypt_password(encrypted)

                self.password_table.insertRow(row_index)

                self.password_table.setItem(row_index, 0, QTableWidgetItem(service))
                self.password_table.setItem(row_index, 1, QTableWidgetItem(login))

                password_item = QTableWidgetItem("••••••••")
                password_item.setData(Qt.UserRole, decrypted)  # Zapamiętaj odszyfrowane hasło
                self.password_table.setItem(row_index, 2, password_item)

                action_widget = QWidget()
                action_layout = QHBoxLayout()
                action_layout.setContentsMargins(0, 0, 0, 0)

                copy_button = QPushButton("📋 Kopiuj")
                reveal_button = QPushButton("👁️ Pokaż/ukryj")
                reveal_button.setCheckable(True)  # Możliwość przełączania
                edit_button = QPushButton("✏️ Edytuj")
                delete_button = QPushButton("🗑️ Usuń")

                # Działania
                copy_button.clicked.connect(lambda _, d=decrypted: self.copy_to_clipboard(d))
                reveal_button.clicked.connect(lambda checked, r=row_index: self.toggle_password_in_table(r, checked))
                edit_button.clicked.connect(lambda _, data=(id_, service, login, decrypted): self.edit_password(data))
                delete_button.clicked.connect(lambda _, data=row: self.delete_password(data))

                for btn in (copy_button, reveal_button, edit_button, delete_button):
                    btn.setFixedSize(120, 30)
                    action_layout.addWidget(btn)

                action_widget.setLayout(action_layout)
                self.password_table.setCellWidget(row_index, 3, action_widget)

            # Stylowanie kolumn
            header = self.password_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się załadować haseł: {str(e)}")
           
    def handle_add_password(self):
        service = self.service_input.text().strip()
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()

        if not service or not login or not password:
            QMessageBox.warning(self, "Brak danych", "Uzupełnij wszystkie pola.")
            return

        try:
            encrypted = encrypt_password(password)
            add_service_to_db(service, login, encrypted)
            QMessageBox.information(self, "Sukces", f"Hasło do {service} zostało dodane.")
            self.clear_add_fields()
            self.load_passwords()  # Odśwież listę
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać hasła: {str(e)}")

    def clear_add_fields(self):
        self.service_input.clear()
        self.login_input.clear()
        self.password_input.clear()

    def copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Skopiowano", "Hasło zostało skopiowane do schowka!")

    def delete_password(self, password_data):
        from database import delete_service_from_db
        confirm = QMessageBox.question(self, "Usuń", f"Czy na pewno usunąć {password_data[1]}?")
        if confirm == QMessageBox.Yes:
            delete_service_from_db(password_data[0])
            self.load_passwords()
    def edit_password(self, password_data):
        self.service_input.setText(password_data[1])
        self.login_input.setText(password_data[2])

        encrypted = password_data[3]
        decrypted = decrypt_password(encrypted)

        self.password_input.setText(decrypted)

        def save_edited():
            from database import update_service_in_db
            new_service = self.service_input.text().strip()
            new_login = self.login_input.text().strip()
            new_pass = encrypt_password(self.password_input.text().strip())
            update_service_in_db(password_data[0], new_service, new_login, new_pass)
            QMessageBox.information(self, "Zapisano", "Zmieniono dane hasła.")
            self.clear_add_fields()
            self.load_passwords()
            self.add_password_button.setText("Dodaj nowe hasło")
            self.add_password_button.clicked.disconnect()
            self.add_password_button.clicked.connect(self.handle_add_password)

        self.add_password_button.setText("Zapisz zmiany")
        self.add_password_button.clicked.disconnect()
        self.add_password_button.clicked.connect(save_edited)

        
    def toggle_password_in_table(self, row, show):
        item = self.password_table.item(row, 2)
        if not item:
            return

        if show:
            encrypted = item.data(Qt.UserRole)
            try:
                password = decrypt_password(encrypted)
                item.setText(password)
            except Exception as e:
                item.setText("[Błąd odszyfrowania]")
                print(f"[Błąd]: {e}")
        else:
            item.setText("••••••••")


    def toggle_password_visibility(self, state):
        if state == Qt.Checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            

    def export_passwords(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Zapisz jako", "", "CSV Files (*.csv)")
        if file_path:
            try:
                from database import export_passwords_to_csv
                export_passwords_to_csv(file_path)
                QMessageBox.information(self, "Sukces", "Hasła zostały wyeksportowane.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się wyeksportować haseł:\n{str(e)}")
    def import_passwords(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Wybierz plik CSV", "", "CSV Files (*.csv)")
        if file_path:
            try:
                from database import import_passwords_from_csv
                import_passwords_from_csv(file_path)
                QMessageBox.information(self, "Sukces", "Hasła zostały zaimportowane.")
                self.load_passwords()
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się zaimportować haseł:\n{str(e)}")


class Setup2FADialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Konfiguracja 2FA")
        self.result = False
        self.setFixedSize(300, 400)

        layout = QVBoxLayout(self)

        # Pokaż QR kod
        qr_path = get_qr_code_image()
        if os.path.exists(qr_path):
            qr_label = QLabel()
            pixmap = QPixmap(qr_path).scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            qr_label.setPixmap(pixmap)
            qr_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(qr_label)
        else:
            layout.addWidget(QLabel("Nie udało się wygenerować QR kodu."))

        layout.addWidget(QLabel("Wprowadź kod z aplikacji:"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Kod 2FA")
        layout.addWidget(self.code_input)

        confirm_button = QPushButton("Potwierdź")
        confirm_button.clicked.connect(self.verify_code)
        layout.addWidget(confirm_button)

    def verify_code(self):
        code = self.code_input.text().strip()
        if verify_code(code):
            self.result = True
            self.accept()
        else:
            QMessageBox.warning(self, "Błąd", "Niepoprawny kod 2FA.")
            
class TwoFactorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Weryfikacja 2FA")
        self.result = False
        self.setFixedSize(300, 150)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Wprowadź kod z aplikacji uwierzytelniającej:"))

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Kod 2FA")
        layout.addWidget(self.code_input)

        confirm_button = QPushButton("Potwierdź")
        confirm_button.clicked.connect(self.verify_code)
        layout.addWidget(confirm_button)

    def verify_code(self):
        code = self.code_input.text().strip()
        if verify_code(code):
            self.result = True
            self.accept()
        else:
            QMessageBox.warning(self, "Błąd", "Niepoprawny kod 2FA.")