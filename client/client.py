import socket
import os
import struct
import pickle
import hashlib
from client.encryption.aes_encryption import aes_encrypt
from client.encryption.dwt_processor import process_image
from shared.crypto_utils import derive_key, sha256_hash, sha512_hash
from shared.key_rotation_manager import KeyRotationManager
from client.utils.file_utils import read_image

SERVER_ADDRESS = ('192.168.141.10', 12345)

sent_directory = "sent"
key_rotation_manager = KeyRotationManager()
password = "secure_password"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def calculate_checksum(data):
    return hashlib.sha256(data).hexdigest()

try:
    client_socket.connect(SERVER_ADDRESS)
    
    files_to_send = sorted(read_image(sent_directory))
    if not files_to_send:
        raise Exception("No files to send")
    
    for filename in files_to_send:
        file_path = os.path.join(sent_directory, filename)
        try:
            should_rotate, similarity, reason = key_rotation_manager.should_rotate_key(file_path)
            if should_rotate:
                password = f"{password}_{filename}"
                password_bytes = password.encode('utf-8')
                password_length = len(password_bytes)
                client_socket.sendall(struct.pack('>I', password_length))
                client_socket.sendall(password_bytes)
            
            filename_bytes = filename.encode('utf-8')
            filename_length = len(filename_bytes)
            client_socket.sendall(struct.pack('>I', filename_length))
            client_socket.sendall(filename_bytes)

            with open(file_path, 'rb') as file:
                data = file.read()
            
            serialized_data = pickle.dumps(data)
            encrypted_data = aes_encrypt(serialized_data, password)
            
            data_length = len(encrypted_data)
            client_socket.sendall(struct.pack('>I', data_length))
            client_socket.sendall(encrypted_data)

        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            continue  # Skip to the next file

    client_socket.sendall(struct.pack('>I', 0))
    input("File transfer complete. Press Enter to close the connection...")
    
    try:
        client_socket.settimeout(2.0)
        close_msg = client_socket.recv(1024)
        if close_msg == b'CLOSE':
            try:
                client_socket.sendall(b'ACK')
            except:
                pass
    except:
        pass

except Exception as e:
    pass
finally:
    try:
        if client_socket:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
    except:
        pass