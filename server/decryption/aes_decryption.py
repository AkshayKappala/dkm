import os
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from shared.crypto_utils import derive_key

def calculate_checksum(data):
    return hashlib.sha256(data).hexdigest()

def aes_decrypt(ciphertext, password):
    key = derive_key(password)
    iv = ciphertext[:16]
    ct = ciphertext[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    decrypted = unpad(cipher.decrypt(ct), AES.block_size)
    return decrypted

def save_decrypted_image(decrypted_data, output_path):
    with open(output_path, 'wb') as file:
        file.write(decrypted_data)

def main():
    encrypted_file_path = 'path/to/encrypted/file'
    output_image_path = 'path/to/output/image'
    password = 'your_password_here'

    with open(encrypted_file_path, 'rb') as file:
        ciphertext = file.read()

    decrypted_data = aes_decrypt(ciphertext, password)
    save_decrypted_image(decrypted_data, output_image_path)

if __name__ == "__main__":
    main()