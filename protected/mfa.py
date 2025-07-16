import os
import pyotp
import qrcode

from paths import get_local_path

MFA_SECRET_PATH = get_local_path("mfa_secret.txt")
QR_OUTPUT_PATH = get_local_path("mfa_qr.png")


def generate_mfa_secret() -> str:
    """Generuje lub zwraca istniejący sekret TOTP."""
    if not os.path.exists(MFA_SECRET_PATH):
        secret = pyotp.random_base32()
        try:
            with open(MFA_SECRET_PATH, "w") as f:
                f.write(secret)
        except Exception as e:
            raise Exception(f"Nie można zapisać sekretu MFA: {e}")
    else:
        with open(MFA_SECRET_PATH, "r") as f:
            secret = f.read().strip()
    return secret


def get_or_create_secret() -> str | None:
    """Zwraca istniejący sekret lub None, jeśli nie istnieje."""
    if os.path.exists(MFA_SECRET_PATH):
        try:
            with open(MFA_SECRET_PATH, "r") as f:
                return f.read().strip()
        except Exception as e:
            raise Exception(f"Nie można odczytać sekretu MFA: {e}")
    return None


def get_qr_code_image(username="user", issuer_name="Password Manager") -> str:
    """Tworzy plik PNG z kodem QR dla aplikacji TOTP (Google Authenticator itp.)."""
    secret = generate_mfa_secret()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer_name)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    try:
        img.save(QR_OUTPUT_PATH)
    except Exception as e:
        raise Exception(f"Nie można zapisać pliku QR: {e}")

    return QR_OUTPUT_PATH


def verify_code(code: str) -> bool:
    """Weryfikuje jednorazowy kod 2FA."""
    secret = get_or_create_secret()
    if not secret:
        return False

    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    except Exception:
        return False
