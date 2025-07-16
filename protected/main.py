import sys
import os
from PyQt5.QtWidgets import QApplication
from ui import PasswordManager
from security_files import decrypt_files, encrypt_files
from database import create_database_if_not_exists
from security import generate_keys
from paths import get_local_path

def main():
    app = QApplication(sys.argv)
    window = PasswordManager()
    window.show()
    exit_code = app.exec_()
    encrypt_files()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()