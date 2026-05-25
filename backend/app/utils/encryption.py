"""AES-256-CBC encryption utilities for sensitive data like API keys."""

import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.core.config import settings


def _get_key() -> bytes:
    """Get the 32-byte AES-256 encryption key from settings.

    Pads or truncates the configured key to exactly 32 bytes.
    """
    key = settings.ENCRYPTION_KEY.encode("utf-8")
    # Ensure exactly 32 bytes for AES-256
    if len(key) < 32:
        key = key.ljust(32, b"\0")
    elif len(key) > 32:
        key = key[:32]
    return key


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string using AES-256-CBC.

    Args:
        plaintext: The string to encrypt.

    Returns:
        Base64-encoded string containing IV + ciphertext.
    """
    if not plaintext:
        return ""

    key = _get_key()
    iv = os.urandom(16)

    # Pad plaintext to AES block size (16 bytes)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    # Encrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # Return IV + ciphertext as base64
    return base64.b64encode(iv + ciphertext).decode("utf-8")


def decrypt_value(ciphertext: str) -> str:
    """Decrypt an AES-256-CBC encrypted string.

    Args:
        ciphertext: Base64-encoded string containing IV + ciphertext.

    Returns:
        The decrypted plaintext string.
    """
    if not ciphertext:
        return ""

    key = _get_key()
    raw = base64.b64decode(ciphertext)

    # Extract IV (first 16 bytes) and ciphertext
    iv = raw[:16]
    encrypted_data = raw[16:]

    # Decrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

    # Remove padding
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()

    return data.decode("utf-8")


def mask_api_key(api_key: str) -> str:
    """Mask an API key, showing only the last 4 characters.

    Args:
        api_key: The full API key string.

    Returns:
        Masked string like '****abcd'.
    """
    if not api_key or len(api_key) <= 4:
        return "****"
    return "****" + api_key[-4:]
