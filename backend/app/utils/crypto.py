"""Crypto utilities for API key encryption and masking.

This module provides a convenience interface for AES-256 encryption
of sensitive data like API keys. It delegates to the encryption module.
"""

from app.utils.encryption import decrypt_value, encrypt_value, mask_api_key


def encrypt_api_key(plain_text: str) -> str:
    """Encrypt an API key using AES-256-CBC.

    Args:
        plain_text: The plaintext API key to encrypt.

    Returns:
        Base64-encoded encrypted string.
    """
    return encrypt_value(plain_text)


def decrypt_api_key(cipher_text: str) -> str:
    """Decrypt an AES-256-CBC encrypted API key.

    Args:
        cipher_text: The encrypted API key string.

    Returns:
        The decrypted plaintext API key.
    """
    return decrypt_value(cipher_text)


__all__ = ["encrypt_api_key", "decrypt_api_key", "mask_api_key"]
