import json
from PyQt5.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QInputDialog
import os

config_file = './config.json'

def get_pin_from_config():
    with open(config_file, 'r') as file:
        config = json.load(file)
        return config.get('pin', '')

class PinManager:
    def __init__(self, parent):
        self.parent = parent

    def check_pin(self):
        try:
            if not os.path.exists(config_file):
                self.create_pin_dialog("Ustaw PIN (min. 4 znaki):", self.save_pin)
            else:
                with open(config_file, 'r') as file:
                    config = json.load(file)
                    if 'pin' in config:
                        self.create_pin_dialog("Wprowadź PIN:", lambda: self.check_entered_pin(config['pin']))
                    else:
                        self.create_pin_dialog("Ustaw PIN (min. 4 znaki):", self.save_pin)
        except Exception as e:
            QMessageBox.critical(self.parent, "Błąd", f"Wystąpił błąd: {str(e)}")
        pass

    def create_pin_dialog_base(self, title, callback):
        self.pin_window = QWidget()
        self.pin_window.setWindowTitle(title)
        layout = QVBoxLayout()

        pin_label = QLabel("PIN:")
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(pin_label)
        layout.addWidget(self.pin_input)

        confirm_button = QPushButton("Potwierdź")
        confirm_button.clicked.connect(callback)
        layout.addWidget(confirm_button)

        self.pin_window.setLayout(layout)
        self.pin_window.show()

    def create_pin_dialog(self, title, callback):
        self.create_pin_dialog_base(title, callback)
        pass

    def save_pin(self):
        pin = self.pin_input.text()
        if len(pin) >= 4:
            config = {'pin': pin}
            with open(config_file, 'w') as file:
                json.dump(config, file)
            QMessageBox.information(self.parent, "Sukces", "PIN został ustawiony.")
            self.pin_window.close()
            self.parent.show()
        else:
            QMessageBox.warning(self.parent, "Błąd", "PIN musi mieć co najmniej 4 znaki.")

    def check_entered_pin(self, expected_pin):
        entered_pin = self.pin_input.text()
        if entered_pin == expected_pin:
            QMessageBox.information(self.parent, "Sukces", "PIN poprawny.")
            self.pin_window.close()
            self.parent.show()
        else:
            QMessageBox.warning(self.parent, "Błąd", "Niepoprawny PIN.")
