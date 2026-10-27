import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def _get_aes_key() -> bytes:
    """Derive a 32-byte key from MASTER_ENCRYPTION_KEY."""
    raw_key = settings.MASTER_ENCRYPTION_KEY
    if len(raw_key) == 64:
        try:
            return bytes.fromhex(raw_key)
        except ValueError:
            pass
    key_bytes = raw_key.encode("utf-8")
    if len(key_bytes) < 32:
        return key_bytes.ljust(32, b"0")
    return key_bytes[:32]


def encrypt_secret(plaintext: str) -> str:
    """Encrypt secret plaintext using AES-256-GCM. Returns base64 encoded string."""
    if not plaintext:
        return ""
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # Standard 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Store nonce + ciphertext
    combined = nonce + ciphertext
    return base64.b64encode(combined).decode("utf-8")


def decrypt_secret(encrypted_b64: str) -> str:
    """Decrypt base64 encoded AES-256-GCM ciphertext."""
    if not encrypted_b64:
        return ""
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    combined = base64.b64decode(encrypted_b64.encode("utf-8"))
    nonce = combined[:12]
    ciphertext = combined[12:]
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted_bytes.decode("utf-8")


def mask_secret(plaintext: str) -> str:
    """Return a masked representation of a secret, e.g. sk-***1234."""
    if not plaintext or len(plaintext) <= 6:
        return "******"
    return f"{plaintext[:3]}***{plaintext[-4:]}"
