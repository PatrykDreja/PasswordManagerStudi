from PyQt5.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QPushButton, QDialog,
    QMessageBox, QDialogButtonBox, QSpinBox, QInputDialog,
    QHeaderView
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from datebase import get_all_services, add_service, get_service, update_service
from security import encrypt_password, decrypt_password
from pin import PinManager
import string
import secrets

class PasswordManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pin_manager = PinManager(self)
        self.setWindowTitle("Menedżer Haseł")
        self.setGeometry(100, 100, 800, 600)
        self.pin_entered = False
        self.pin_manager.check_pin()
        self.hide()
        self.setup_ui()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        big_label = QLabel("Menedżer Haseł")
        big_label.setAlignment(Qt.AlignCenter)
        big_font = big_label.font()
        big_font.setPointSize(20)
        big_label.setFont(big_font)
        self.layout.addWidget(big_label)

        self.setStyleSheet("""
        QTreeWidgetItem{
                padding: 5px;
                font-size: 16px;
                font-weight: bold;
        }
        QLabel {
            color: #333;
            font-size: 20px;
            font-weight: bold;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: 1px solid #4CAF50;
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 16px;
        }
        QLineEdit, QSpinBox {
            padding: 5px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        QSpinBox{
            padding: 5px;
        }
        """)

        change_pin_button = QPushButton("Zmień PIN")
        change_pin_button.clicked.connect(self.pin_manager.check_pin)
        self.layout.addWidget(change_pin_button)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Szukaj nazwy strona/aplikacja")
        self.search_input.textChanged.connect(self.filter_tree)
        self.layout.addWidget(self.search_input)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(['Nazwa strona/aplikacja'])

        header_font = self.tree.headerItem().font(0)
        header_font.setPointSize(18)
        self.tree.header().setFont(header_font)
        self.tree.header().setStyleSheet("""
            background-color: #4CAF50;
            color: black;
        """)
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.layout.addWidget(self.tree)
        
        self.populate_tree()

        add_button = QPushButton("Dodaj nową strona/aplikacja")
        add_button.clicked.connect(self.open_add_dialog)
        self.layout.addWidget(add_button)

        edit_button = QPushButton("Edytuj nazwe strona/aplikacja")
        edit_button.clicked.connect(self.edit_selected_service)
        self.layout.addWidget(edit_button)

        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #f0f0f0;
                font-size: 16px;
            }
        """)

        self.setFont(QFont("Arial", 12))

    def filter_tree(self):
        search_text = self.search_input.text().lower()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            service_name = item.text(0).lower()
            item.setHidden(search_text not in service_name)

    def populate_tree(self):
        self.tree.clear()
        try:
            rows = get_all_services()
            for row in rows:
                item = QTreeWidgetItem([row[1]])
                item.setData(0, Qt.UserRole, row[0])
                self.tree.addTopLevelItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania danych: {str(e)}")

    def open_add_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Dodaj nową strona/aplikacja")
        layout = QVBoxLayout()

        service_label = QLabel("Nazwa strona/aplikacja:")
        self.service_input = QLineEdit()
        layout.addWidget(service_label)
        layout.addWidget(self.service_input)

        login_label = QLabel("Login:")
        self.login_input = QLineEdit()
        layout.addWidget(login_label)
        layout.addWidget(self.login_input)

        password_label = QLabel("Hasło:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)

        generate_password_button = QPushButton("Generuj hasło")
        generate_password_button.clicked.connect(self.generate_password)
        layout.addWidget(generate_password_button)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.add_service)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.exec_()

    def generate_password(self):
        length, ok = QInputDialog.getInt(self, "Długość hasła", "Podaj długość hasła (8-32):", 12, 8, 32)
        if ok:
            include_uppercase, ok1 = QInputDialog.getItem(self, "Znaki specjalne", "Czy chcesz uwzględnić wielkie litery?", ["Tak", "Nie"], 0, False)
            include_numbers, ok2 = QInputDialog.getItem(self, "Cyfry", "Czy chcesz uwzględnić cyfry?", ["Tak", "Nie"], 0, False)
            include_special, ok3 = QInputDialog.getItem(self, "Znaki specjalne", "Czy chcesz uwzględnić znaki specjalne?", ["Tak", "Nie"], 0, False)

            if all([ok1, ok2, ok3]):
                characters = string.ascii_lowercase
                if include_uppercase == "Tak":
                    characters += string.ascii_uppercase
                if include_numbers == "Tak":
                    characters += string.digits
                if include_special == "Tak":
                    characters += string.punctuation

                password = ''.join(secrets.choice(characters) for i in range(length))
                self.password_input.setText(password)

    def add_service(self):
        service = self.service_input.text()
        login = self.login_input.text()
        password = self.password_input.text()
        if service and login and password:
            try:
                encrypted_password = encrypt_password(password)
                add_service(service, login, encrypted_password)
                self.populate_tree()
                QMessageBox.information(self, "Sukces", "Strona/aplikacja została dodana.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas dodawania strona/aplikacja: {str(e)}")
        else:
            QMessageBox.warning(self, "Błąd", "Wszystkie pola są wymagane.")

    def edit_selected_service(self):
        selected_item = self.tree.currentItem()
        if selected_item:
            service_id = selected_item.data(0, Qt.UserRole)
            dialog = QDialog(self)
            dialog.setWindowTitle("Edytuj strona/aplikacja")
            layout = QVBoxLayout()

            service_label = QLabel("Nazwa strona/aplikacja:")
            self.service_input = QLineEdit()
            layout.addWidget(service_label)
            layout.addWidget(self.service_input)

            login_label = QLabel("Login:")
            self.login_input = QLineEdit()
            layout.addWidget(login_label)
            layout.addWidget(self.login_input)

            password_label = QLabel("Hasło:")
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            layout.addWidget(password_label)
            layout.addWidget(self.password_input)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(lambda: self.update_service(service_id))
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            dialog.setLayout(layout)

            service = get_service(service_id)
            if service:
                self.service_input.setText(service[0])
                self.login_input.setText(service[1])
                self.password_input.setText(decrypt_password(service[2]))

            dialog.exec_()
        else:
            QMessageBox.warning(self, "Błąd", "Wybierz strona/aplikacja do edycji.")

    def update_service(self, service_id):
        service = self.service_input.text()
        login = self.login_input.text()
        password = self.password_input.text()
        if service and login and password:
            try:
                encrypted_password = encrypt_password(password)
                update_service(service_id, service, login, encrypted_password)
                self.populate_tree()
                QMessageBox.information(self, "Sukces", "Strona/aplikacja została zaktualizowana.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas aktualizacji strona/aplikacja: {str(e)}")
        else:
            QMessageBox.warning(self, "Błąd", "Wszystkie pola są wymagane.")
