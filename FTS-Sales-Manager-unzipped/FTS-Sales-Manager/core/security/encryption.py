# -*- coding: utf-8 -*-
"""
core/security/encryption.py

مدير التشفير للبيانات الحساسة
"""

import hashlib
import secrets
from cryptography.fernet import Fernet
import os
import base64
import json
from typing import Tuple, Optional

from core.logger import logger


class EncryptionManager:
    """مدير التشفير الآمن للبيانات"""

    def __init__(self, key_file: str = "data/.encryption_key"):
        """
        Initialize encryption manager

        Args:
            key_file: Path to encryption key file
        """
        self.key_file = key_file
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)

    def _get_or_create_key(self) -> bytes:
        """الحصول على مفتاح التشفير أو إنشاؤه"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                    # Validate key
                    Fernet(key)  # This will raise if invalid
                    return key

            # Create new key
            key = Fernet.generate_key()

            # Save key securely
            os.makedirs(os.path.dirname(self.key_file), exist_ok=True)

            # Set restrictive permissions on Unix-like systems
            if os.name != 'nt':  # Not Windows
                os.chmod(os.path.dirname(self.key_file), 0o700)

            with open(self.key_file, 'wb') as f:
                f.write(key)

            # Set file permissions
            if os.name != 'nt':
                os.chmod(self.key_file, 0o600)

            logger.info("Created new encryption key")
            return key

        except Exception as e:
            logger.error(f"Error managing encryption key: {e}")
            # Generate temporary key (not persistent)
            return Fernet.generate_key()

    def encrypt_data(self, data: str) -> str:
        """
        تشفير البيانات

        Args:
            data: String data to encrypt

        Returns:
            Base64 encoded encrypted data
        """
        try:
            encrypted = self.cipher.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        فك تشفير البيانات

        Args:
            encrypted_data: Base64 encoded encrypted data

        Returns:
            Decrypted string data
        """
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise

    def encrypt_json(self, data: dict) -> str:
        """
        تشفير بيانات JSON

        Args:
            data: Dictionary to encrypt

        Returns:
            Encrypted JSON string
        """
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt_data(json_str)

    def decrypt_json(self, encrypted_data: str) -> dict:
        """
        فك تشفير بيانات JSON

        Args:
            encrypted_data: Encrypted JSON string

        Returns:
            Decrypted dictionary
        """
        json_str = self.decrypt_data(encrypted_data)
        return json.loads(json_str)

    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
        """
        تشفير كلمة المرور باستخدام PBKDF2

        Args:
            password: Password to hash
            salt: Optional salt (will generate if not provided)

        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(32)

        # Use PBKDF2 with SHA256
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000,  # iterations
            dklen=64  # 64 bytes = 512 bits
        )

        # Return base64 encoded hash and salt
        return base64.b64encode(hashed).decode('utf-8'), salt

    def verify_password(self, password: str, hashed: str, salt: bytes) -> bool:
        """
        التحقق من كلمة المرور

        Args:
            password: Password to verify
            hashed: Base64 encoded hashed password
            salt: Salt used for hashing

        Returns:
            True if password matches
        """
        new_hash, _ = self.hash_password(password, salt)
        return secrets.compare_digest(new_hash, hashed)

    def generate_token(self, length: int = 32) -> str:
        """
        Generate secure random token

        Args:
            length: Token length in bytes

        Returns:
            URL-safe base64 encoded token
        """
        return secrets.token_urlsafe(length)

    def rotate_key(self) -> bool:
        """
        Rotate encryption key (requires re-encrypting all data)

        Returns:
            True if successful
        """
        try:
            # Generate new key
            new_key = Fernet.generate_key()
            new_cipher = Fernet(new_key)

            # Save old key for rollback
            old_key = self.key

            # Update key
            self.key = new_key
            self.cipher = new_cipher

            # Save new key
            with open(self.key_file, 'wb') as f:
                f.write(new_key)

            logger.info("Encryption key rotated successfully")
            return True

        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            return False