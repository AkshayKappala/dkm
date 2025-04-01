import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from shared.crypto_utils import derive_key

def aes_decrypt(ciphertext, password):
    """Decrypts the given ciphertext using AES-256 encryption."""
    key = derive_key(password)  # Derive the key using the provided password
    cipher = AES.new(key, AES.MODE_CBC, iv=ciphertext[:16])
    decrypted = unpad(cipher.decrypt(ciphertext[16:]), AES.block_size)
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