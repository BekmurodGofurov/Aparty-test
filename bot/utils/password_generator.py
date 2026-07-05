import secrets
import string
import hashlib


def generate_password(length: int = 10) -> str:
    """Generate a random password with letters, numbers, and symbols"""
    characters = string.ascii_letters + string.digits + string.punctuation.replace('"', '').replace("'", '')
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()
