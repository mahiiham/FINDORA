import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def _fernet():
    digest = hashlib.sha256(current_app.config['SECRET_KEY'].encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def protect_text(value: str) -> str:
    if not value:
        return ''
    return _fernet().encrypt(value.encode()).decode()


def reveal_text(value: str) -> str:
    if not value:
        return ''
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        return '[unavailable]'
