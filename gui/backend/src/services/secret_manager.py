"""Secret management with AES-256-GCM encryption."""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import settings


class SecretManager:
    """Manages encrypted secrets."""

    def __init__(self):
        key = settings.encryption_key.encode()
        if len(key) < 32:
            key = key.ljust(32, b"0")
        self.aesgcm = AESGCM(key[:32])

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt a secret value."""
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        return nonce + ciphertext

    def decrypt(self, encrypted: bytes) -> str:
        """Decrypt a secret value."""
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()


secret_manager = SecretManager()
