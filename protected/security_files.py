from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
import os
from paths import get_local_path
import time
import sqlite3
import win32crypt
_active_connection = None
FILES_TO_ENCRYPT = [
    "baza_hasel.db",
    "config.json",
    "mfa_qr.png",
    "mfa_secret.txt"
]

rsa_pub = get_local_path("rsa_pub.pem.enc")
rsa_priv = get_local_path("rsa_priv.pem.enc")


def load_private_key():
    if not os.path.exists(rsa_priv):
        raise FileNotFoundError("Brak zaszyfrowanego klucza prywatnego.")
    with open(rsa_priv, 'rb') as f:
        encrypted = f.read()
    try:
        decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
    except Exception as e:
        raise ValueError(f"Nie udało się odszyfrować klucza prywatnego: {e}")
    return RSA.import_key(decrypted)

def load_public_key():
    if not os.path.exists(rsa_pub):
        raise FileNotFoundError("Brak zaszyfrowanego klucza publicznego.")
    with open(rsa_pub, 'rb') as f:
        encrypted = f.read()
    try:
        decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
    except Exception as e:
        raise ValueError(f"Nie udało się odszyfrować klucza publiczenego: {e}")
    return RSA.import_key(decrypted)


def encrypt_file(path):
    try:
        print(f"[SZYFRUJĘ] {os.path.basename(path)}")
        public_key = load_public_key()
        rsa_cipher = PKCS1_OAEP.new(public_key)

        aes_key = get_random_bytes(32)
        aes_cipher = AES.new(aes_key, AES.MODE_GCM)
        nonce = aes_cipher.nonce

        with open(path, 'rb') as f:
            plaintext = f.read()

        ciphertext, tag = aes_cipher.encrypt_and_digest(plaintext)
        encrypted_key = rsa_cipher.encrypt(aes_key)

        with open(path + '.enc', 'wb') as f:
            f.write(len(encrypted_key).to_bytes(2, 'big'))
            f.write(encrypted_key)
            f.write(nonce)
            f.write(tag)
            f.write(ciphertext)

        os.remove(path)
    except Exception as e:
        print(f"Błąd podczas szyfrowania {path}: {e}")


def decrypt_file(path_enc):
    time.sleep(0.5)
    try:
        print(f"[ODSZYFRUJĘ] {os.path.basename(path_enc)}")
        private_key = load_private_key()
        rsa_cipher = PKCS1_OAEP.new(private_key)

        with open(path_enc, 'rb') as f:
            key_len = int.from_bytes(f.read(2), 'big')
            encrypted_key = f.read(key_len)
            nonce = f.read(16)
            tag = f.read(16)
            ciphertext = f.read()

        aes_key = rsa_cipher.decrypt(encrypted_key)
        aes_cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        plaintext = aes_cipher.decrypt_and_verify(ciphertext, tag)

        path = path_enc.replace('.enc', '')
        with open(path, 'wb') as f:
            f.write(plaintext)

        os.remove(path_enc)
    except Exception as e:
        print(f"Błąd podczas odszyfrowywania {path_enc}: {e}")


def encrypt_files():
    for filename in FILES_TO_ENCRYPT:
        path = get_local_path(filename)
        if os.path.exists(path) and not path.endswith('.enc'):
            encrypt_file(path)


def decrypt_files():
    for filename in FILES_TO_ENCRYPT:
        path = get_local_path(filename)
        enc_path = path + '.enc'

        if os.path.exists(enc_path):

            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Nie można usunąć istniejącego {path}: {e}")
                    continue
            decrypt_file(enc_path)

def close_connection():
    global _active_connection
    if _active_connection:
        _active_connection.close()
        _active_connection = None

def close_db_and_encrypt():


    close_connection()
    time.sleep(5)
    encrypt_files()