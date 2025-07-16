# qrcode_setup.py
import qrcode
from mfa import generate_secret, get_totp_uri

secret = generate_secret()
uri = get_totp_uri(secret)
img = qrcode.make(uri)
img.show()  # Pokazuje QR kod do zeskanowania
