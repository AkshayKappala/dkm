import os
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def generate_aes_key(password):
    """
    Generate a 256-bit AES key from a given password using SHA-256.
    
    Args:
        password (str): The password to derive the AES key from.
        
    Returns:
        bytes: The derived AES key.
    """
    sha256_hash = hashlib.sha256(password.encode()).digest()
    return sha256_hash

def encrypt_image_fragment(fragment, password):
    """
    Encrypt an image fragment using AES-256 encryption.
    
    Args:
        fragment (bytes): The image fragment to encrypt.
        password (str): The password to derive the AES key from.
        
    Returns:
        bytes: The encrypted image fragment.
    """
    aes_key = generate_aes_key(password)
    cipher = AES.new(aes_key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(fragment, AES.block_size))
    return cipher.iv + ct_bytes  # Prepend IV for decryption

def decrypt_image_fragment(encrypted_fragment, password):
    """
    Decrypt an encrypted image fragment using AES-256 decryption.
    
    Args:
        encrypted_fragment (bytes): The encrypted image fragment to decrypt.
        password (str): The password to derive the AES key from.
        
    Returns:
        bytes: The decrypted image fragment.
    """
    aes_key = generate_aes_key(password)
    iv = encrypted_fragment[:AES.block_size]  # Extract the IV
    ct = encrypted_fragment[AES.block_size:]  # Extract the ciphertext
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    decrypted_fragment = unpad(cipher.decrypt(ct), AES.block_size)
    return decrypted_fragment