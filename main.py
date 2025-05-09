import sys
from PyQt5.QtWidgets import QApplication
from ui import PasswordManager
from database import create_database_if_not_exists
from security import generate_key, hide_files
from pin import PinManager

def main():
    if create_database_if_not_exists():
        generate_key()
        hide_files()

    app = QApplication(sys.argv)
    window = PasswordManager()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
