import json
import csv
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QLabel, QMessageBox, QTreeWidget, QTreeWidgetItem, QMenu,
    QDialog, QTextEdit, QPushButton, QApplication, QCheckBox,
    QTableWidget, QTableWidgetItem, QHBoxLayout, QFileDialog, QHeaderView
)
from PyQt5.QtCore import Qt

from database import fetch_all_passwords, add_service_to_db
from security import encrypt_password, generate_key, decrypt_password

config_file = './config.json'


class PasswordManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔐 Menedżer Haseł")
        self.setGeometry(100, 100, 1000, 700)

        self.pin_entered = False
        self.setup_ui()
        generate_key()  # Upewnij się, że klucz do szyfrowania istnieje

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

        if not os.path.exists(config_file):
            self.save_pin(entered_pin)
            QMessageBox.information(self, "Ustawiono PIN", "Nowy PIN został zapisany.")
            self.unlock_ui()
        else:
            saved_pin = self.get_saved_pin()
            if entered_pin == saved_pin:
                self.unlock_ui()
                QMessageBox.information(self, "Sukces", "PIN poprawny!")
            else:
                QMessageBox.warning(self, "Błąd", "Niepoprawny PIN.")

    def save_pin(self, pin):
        try:
            with open(config_file, 'w') as file:
                json.dump({'pin': pin}, file)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać PIN-u: {str(e)}")

    def get_saved_pin(self):
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)
                return config.get('pin', '')
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się odczytać PIN-u: {str(e)}")
            return ""

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
                self.password_table.setColumnWidth(3, 300)
                self.password_table.insertRow(row_index)
                self.password_table.setItem(row_index, 0, QTableWidgetItem(service))
                self.password_table.setItem(row_index, 1, QTableWidgetItem(login))
                self.password_table.setItem(row_index, 2, QTableWidgetItem("••••••••"))

                # Akcje
                action_widget = QWidget()
                action_layout = QHBoxLayout()
                action_layout.setContentsMargins(0, 0, 0, 0)
                
                show_button = QPushButton("📋 Kopiuj")
                reveal_button = QPushButton("👁️ Pokaż")
                edit_button = QPushButton("✏️ Edytuj")
                delete_button = QPushButton("🗑️ Usuń")

                show_button.clicked.connect(lambda _, d=decrypted: self.copy_to_clipboard(d))
                reveal_button.clicked.connect(lambda _, data=row: self.toggle_password_visibility(data))
                edit_button.clicked.connect(lambda _, data=row: self.edit_password(data))
                delete_button.clicked.connect(lambda _, data=row: self.delete_password(data))

                for btn in (show_button, reveal_button, edit_button, delete_button):
                    btn.setFixedSize(80, 30)
                    action_layout.addWidget(btn)

                action_widget.setLayout(action_layout)
                self.password_table.setCellWidget(row_index, 3, action_widget)

            # Ulepsz wygląd kolumn
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
        decrypted = decrypt_password(password_data[3])
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
            password = item.data(Qt.UserRole)  # pobierz zapisane hasło
            item.setText(password)
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
