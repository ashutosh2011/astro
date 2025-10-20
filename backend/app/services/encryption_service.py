"""Encryption service for field-level encryption."""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import settings
from app.utils.errors import ValidationError


class EncryptionService:
    """Service for field-level encryption using Fernet."""
    
    def __init__(self, encryption_key: str = None):
        """Initialize encryption service."""
        self.encryption_key = encryption_key or settings.encryption_key
        self._fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet instance from encryption key."""
        try:
            # If key is base64 encoded, decode it
            if len(self.encryption_key) == 44 and self.encryption_key.endswith('='):
                key_bytes = base64.b64decode(self.encryption_key)
            else:
                # Derive key from password using PBKDF2
                salt = b'astro_mvp_salt'  # In production, use random salt per encryption
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key_bytes = kdf.derive(self.encryption_key.encode())
            
            return Fernet(base64.urlsafe_b64encode(key_bytes))
        except Exception as e:
            raise ValidationError(f"Failed to initialize encryption: {str(e)}")
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string value."""
        if not data:
            return data
        
        try:
            encrypted_bytes = self._fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            raise ValidationError(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string value."""
        if not encrypted_data:
            return encrypted_data
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValidationError(f"Decryption failed: {str(e)}")
    
    def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """Encrypt specific fields in a dictionary."""
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field] is not None:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """Decrypt specific fields in a dictionary."""
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field] is not None:
                decrypted_data[field] = self.decrypt(str(decrypted_data[field]))
        
        return decrypted_data


# Global encryption service instance
encryption_service = EncryptionService()

