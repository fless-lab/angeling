import base64
import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

class Crypter:
    def __init__(self, key=None):
        self.key = key if key else get_random_bytes(32)
        
    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        iv = get_random_bytes(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(pad(data, AES.block_size))
        return base64.b85encode(iv + encrypted)
        
    def decrypt(self, encrypted_data):
        raw = base64.b85decode(encrypted_data)
        iv = raw[:16]
        encrypted = raw[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
        return decrypted
        
    def encrypt_file(self, file_path):
        with open(file_path, 'rb') as f:
            data = f.read()
        return self.encrypt(data)
        
    def decrypt_file(self, encrypted_data, output_path=None):
        decrypted = self.decrypt(encrypted_data)
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(decrypted)
        return decrypted
