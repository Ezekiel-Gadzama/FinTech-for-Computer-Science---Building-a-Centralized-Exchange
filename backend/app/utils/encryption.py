"""Enhanced encryption utilities for wallet private keys"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
from flask import current_app


def get_encryption_key():
    """Get or generate encryption key from app config"""
    secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Derive a key from the secret key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'crypto_exchange_salt',  # In production, use a unique salt per user
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return key


def encrypt_private_key(private_key: str) -> str:
    """Encrypt a private key using Fernet symmetric encryption"""
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(private_key.encode())
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")


def decrypt_private_key(encrypted_key: str) -> str:
    """Decrypt a private key"""
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_key.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


def generate_encryption_key() -> str:
    """Generate a new encryption key (for cold wallet storage)"""
    return Fernet.generate_key().decode('utf-8')

