from cryptography.fernet import Fernet
import os

key_file = './key.key'

def load_key():
    return open(key_file, "rb").read()

def generate_key():
    if not os.path.exists(key_file):
        key = Fernet.generate_key()
        with open(key_file, "wb") as key_file_obj:
            key_file_obj.write(key)
    else:
        print("Klucz już istnieje.")

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
