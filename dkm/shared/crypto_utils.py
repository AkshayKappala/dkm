import hashlib
import os

def generate_sha256_hash(data):
    """Generate a SHA-256 hash of the given data."""
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()

def generate_sha512_hash(data):
    """Generate a SHA-512 hash of the given data."""
    sha512 = hashlib.sha512()
    sha512.update(data)
    return sha512.hexdigest()

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