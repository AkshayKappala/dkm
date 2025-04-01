import hashlib
import os

def derive_key(password):
    """Derives a 256-bit key from the given password using SHA-256."""
    return hashlib.sha256(password.encode()).digest()

def sha256_hash(data):
    """Generates a SHA-256 hash of the given data."""
    return hashlib.sha256(data).digest()

def sha512_hash(data):
    """Generates a SHA-512 hash of the given data."""
    return hashlib.sha512(data).digest()

def derive_key_from_hash(hash_value):
    """Derive a key from the SHA-256 hash value."""
    return hash_value[:32]  # Use the first 32 bytes for AES-256 key

def xor_data(data1, data2):
    """Perform XOR operation between two byte arrays."""
    return bytes(a ^ b for a, b in zip(data1, data2))

def save_hash_to_file(hash_value, file_path):
    """Save the generated hash to a file."""
    with open(file_path, 'w') as f:
        f.write(hash_value)

def load_hash_from_file(file_path):
    """Load a hash from a file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read().strip()
    return None