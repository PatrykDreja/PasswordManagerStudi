import os
from cryptography.fernet import Fernet
import ctypes
import win32crypt

key_file = './key.key'
config_file = './config.json'
db_file = './baza_hasel.db'


def protect_key(key):
    return win32crypt.CryptProtectData(key, None, None, None, None, 0)

def unprotect_key(protected_key):
    return win32crypt.CryptUnprotectData(protected_key, None, None, None, 0)[1]


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
        protected_key = protect_key(key)  
        with open(key_file, "wb") as key_file_write:
            key_file_write.write(protected_key)  

def load_key():
    with open(key_file, "rb") as key_file_read:
        protected_key = key_file_read.read()
    return unprotect_key(protected_key)  


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


def encrypt_file(file_path):
    key = load_key()  
    fernet = Fernet(key)
    with open(file_path, 'rb') as file:
        file_data = file.read()
    encrypted_data = fernet.encrypt(file_data)
    with open(file_path, 'wb') as file:
        file.write(encrypted_data)

def decrypt_file(file_path):
    key = load_key()
    fernet = Fernet(key)
    with open(file_path, 'rb') as file:
        encrypted_data = file.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    with open(file_path, 'wb') as file:
        file.write(decrypted_data)

def set_file_permissions(file_path):
    if os.path.exists(file_path):
        os.chmod(file_path, 0o600) 