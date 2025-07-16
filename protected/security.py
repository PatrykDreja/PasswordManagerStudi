import os
import json
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from paths import get_local_path
import win32crypt

# Ścieżki
rsa_pub = get_local_path("rsa_pub.pem.enc")
rsa_priv = get_local_path("rsa_priv.pem.enc")
config_file = get_local_path("config.json")

# ---------------- KLUCZE ----------------

def generate_keys():
    if os.path.exists(rsa_priv) and os.path.exists(rsa_pub):
        return
    key = RSA.generate(2048)

    private_data = key.export_key()
    encrypted_priv = win32crypt.CryptProtectData(private_data, None, None, None, None, 0)
    with open(get_local_path("rsa_priv.pem.enc"), 'wb') as f:
        f.write(encrypted_priv)

    public_data = key.publickey().export_key()
    encrypted_pub = win32crypt.CryptProtectData(public_data, None, None, None, None, 0)
    with open(get_local_path("rsa_pub.pem.enc"), 'wb') as f:
        f.write(encrypted_pub)

def load_private_key():
    if not os.path.exists(rsa_priv):
        raise FileNotFoundError("Brak zaszyfrowanego klucza prywatnego.")
    with open(rsa_priv, 'rb') as f:
        encrypted = f.read()
    try:
        decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
    except Exception as e:
        raise ValueError(f"Nie udało się odszyfrować klucza prywatnego securyty: {e}")
    return RSA.import_key(decrypted)

def load_public_key():
    if not os.path.exists(rsa_pub):
        raise FileNotFoundError("Brak zaszyfrowanego klucza publicznego.")
    with open(rsa_pub, 'rb') as f:
        encrypted = f.read()
    try:
        decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
    except Exception as e:
        raise ValueError(f"Nie udało się odszyfrować klucza publiczenego securyty: {e}")
    return RSA.import_key(decrypted)

# ---------------- PIN (krótki, RSA-only) ----------------

def encrypt_data(data: str) -> str:
    public_key = load_public_key()
    cipher = PKCS1_OAEP.new(public_key)
    encrypted = cipher.encrypt(data.encode())
    return encrypted.hex()

def decrypt_data(hex_data: str) -> str:
    private_key = load_private_key()
    encrypted = bytes.fromhex(hex_data)
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(encrypted).decode()

def save_pin(pin: str):
    try:
        encrypted_pin = encrypt_data(pin)
        with open(config_file, 'w') as file:
            json.dump({'pin': encrypted_pin}, file)
    except Exception as e:
        print(f"[Błąd] Nie udało się zapisać PIN-u: {e}")

def get_saved_pin() -> str:
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
            return decrypt_data(config.get('pin', ''))
    except Exception as e:
        print(f"[Błąd] Nie udało się odczytać PIN-u: {e}")
        return ""

# ---------------- HASŁA (RSA + AES → base64) ----------------

def encrypt_password(plaintext: str) -> str:
    aes_key = get_random_bytes(32)
    cipher_aes = AES.new(aes_key, AES.MODE_GCM)
    ciphertext, tag = cipher_aes.encrypt_and_digest(plaintext.encode('utf-8'))
    nonce = cipher_aes.nonce

    cipher_rsa = PKCS1_OAEP.new(load_public_key())
    encrypted_key = cipher_rsa.encrypt(aes_key)

    payload = (
        len(encrypted_key).to_bytes(2, 'big') +
        encrypted_key +
        nonce +
        tag +
        ciphertext
    )
    return base64.b64encode(payload).decode('utf-8')  # do zapisania jako TEXT w SQLite

def decrypt_password(encoded_data: str) -> str:
    try:
        encrypted_data = base64.b64decode(encoded_data)
        key_len = int.from_bytes(encrypted_data[:2], 'big')
        offset = 2

        encrypted_key = encrypted_data[offset:offset + key_len]
        offset += key_len

        nonce = encrypted_data[offset:offset + 16]
        offset += 16

        tag = encrypted_data[offset:offset + 16]
        offset += 16

        ciphertext = encrypted_data[offset:]

        cipher_rsa = PKCS1_OAEP.new(load_private_key())
        aes_key = cipher_rsa.decrypt(encrypted_key)

        cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher_aes.decrypt_and_verify(ciphertext, tag)

        return plaintext.decode('utf-8')
    except Exception as e:
        raise Exception(f"Błąd deszyfrowania hasła: {e}")
    

