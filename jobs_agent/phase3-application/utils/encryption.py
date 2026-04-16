"""
Encryption utilities for sensitive data (passwords, API keys)
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from pathlib import Path
import json


class Encryptor:
    """
    Simple encryption for sensitive data
    """
    
    def __init__(self, password: str = None):
        """
        Initialize encryptor with password
        If no password provided, generates one
        """
        key_file = Path("data/.encryption_key")
        
        if key_file.exists():
            # Load existing key
            self.key = key_file.read_bytes()
        else:
            # Generate new key
            if password is None:
                password = base64.urlsafe_b64encode(os.urandom(32)).decode()
                print(f"⚠️  Generated encryption password: {password}")
                print("   Save this password securely!")
            
            self.key = self._generate_key(password)
            
            # Save key (in production, use more secure storage)
            key_file.parent.mkdir(exist_ok=True)
            key_file.write_bytes(self.key)
            key_file.chmod(0o600)  # Read/write for owner only
        
        self.cipher = Fernet(self.key)
    
    def _generate_key(self, password: str) -> bytes:
        """Generate encryption key from password"""
        
        salt = b'job_application_salt'  # In production, use random salt
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()
    
    def encrypt_dict(self, data: dict) -> str:
        """Encrypt dictionary"""
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt to dictionary"""
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)


# Example usage
if __name__ == "__main__":
    encryptor = Encryptor()
    
    # Encrypt password
    password = "my_secret_password"
    encrypted = encryptor.encrypt(password)
    print(f"Encrypted: {encrypted}")
    
    # Decrypt
    decrypted = encryptor.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")
    
    # Encrypt credentials
    credentials = {
        "linkedin_username": "john@example.com",
        "linkedin_password": "secret123"
    }
    
    encrypted_creds = encryptor.encrypt_dict(credentials)
    print(f"\nEncrypted credentials: {encrypted_creds}")
    
    decrypted_creds = encryptor.decrypt_dict(encrypted_creds)
    print(f"Decrypted credentials: {decrypted_creds}")