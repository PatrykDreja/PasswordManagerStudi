import sys
from PyQt5.QtWidgets import QApplication
from ui import PasswordManager
from database import create_database_if_not_exists
from security import generate_key, hide_files, unhide_files

def main():
    if create_database_if_not_exists():
        generate_key()
        hide_files()
    
    unhide_files()
    app = QApplication(sys.argv)
    window = PasswordManager()
    window.show()
    sys.exit(app.exec_(), hide_files)

if __name__ == "__main__":
    main()
