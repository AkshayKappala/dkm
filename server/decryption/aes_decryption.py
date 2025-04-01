import os
import hashlib  # Add this import for checksum calculation
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from shared.crypto_utils import derive_key

def calculate_checksum(data):
    """Calculate and return the SHA-256 checksum of the given data."""
    return hashlib.sha256(data).hexdigest()

def aes_decrypt(ciphertext, password):
    """Decrypts the given ciphertext using AES-256 encryption."""
    key = derive_key(password)  # Derive the key using the provided password
    iv = ciphertext[:16]
    ct = ciphertext[16:]
    print(f"[DEBUG] AES Decryption - IV: {iv.hex()}, Ciphertext Length: {len(ct)}")
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    decrypted = unpad(cipher.decrypt(ct), AES.block_size)

    # Log checksum of decrypted data
    checksum = calculate_checksum(decrypted)
    print(f"[DEBUG] Decrypted data checksum: {checksum}")

    return decrypted

def save_decrypted_image(decrypted_data, output_path):
    """Saves the decrypted image data to the specified output path."""
    with open(output_path, 'wb') as file:
        file.write(decrypted_data)

def main():
    # Example usage
    encrypted_file_path = 'path/to/encrypted/file'
    output_image_path = 'path/to/output/image'
    password = 'your_password_here'

    with open(encrypted_file_path, 'rb') as file:
        ciphertext = file.read()

    decrypted_data = aes_decrypt(ciphertext, password)
    save_decrypted_image(decrypted_data, output_image_path)
    print(f"Decrypted image saved to {output_image_path}")

if __name__ == "__main__":
    main()