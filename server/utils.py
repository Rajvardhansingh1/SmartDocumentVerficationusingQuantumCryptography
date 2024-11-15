from cryptography.fernet import Fernet
import hashlib
import base64

def generate_key():
    return Fernet.generate_key()

def encrypt_document(key, data):
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)
    return base64.b64encode(encrypted_data).decode('utf-8')

def decrypt_document(key, encrypted_data):
    fernet = Fernet(key)
    encrypted_data = base64.b64decode(encrypted_data.encode('utf-8'))
    return fernet.decrypt(encrypted_data)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
