import os
from cryptography.fernet import Fernet
import ctypes

key_file = './key.key'
config_file = './config.json'
db_file = './baza_hasel.db'

def hide_file(file_path):
    if os.path.exists(file_path):
        ctypes.windll.kernel32.SetFileAttributesW(file_path, 2)

def unhide_file(file_path):
    if os.path.exists(file_path):
        ctypes.windll.kernel32.SetFileAttributesW(file_path, 0)

def hide_files():
    files_to_hide = [key_file, db_file, config_file]
    for file_path in files_to_hide:
        hide_file(file_path)

def unhide_files():
    files_to_unhide = [key_file, db_file, config_file]
    for file_path in files_to_unhide:
        unhide_file(file_path)

def generate_key():
    if not os.path.exists(key_file):
        key = Fernet.generate_key()
        with open(key_file, "wb") as key_file_write:
            key_file_write.write(key)

def load_key():
    return open(key_file, "rb").read()

def encrypt_password(password):
    key = load_key()
    fernet = Fernet(key)
    encrypted_password = fernet.encrypt(password.encode())
    return encrypted_password.decode()

def decrypt_password(encrypted_password):
    key = load_key()
    fernet = Fernet(key)
    decrypted_password = fernet.decrypt(encrypted_password.encode())
    return decrypted_password.decode()
