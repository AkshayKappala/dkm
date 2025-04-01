import socket
import os
import struct
import pickle
import hashlib
from server.decryption.aes_decryption import aes_decrypt
from shared.key_rotation_manager import KeyRotationManager

SERVER_ADDRESS = ('192.168.141.10', 12345)
received_directory = "received"
os.makedirs(received_directory, exist_ok=True)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

password = "secure_password"
key_rotation_manager = KeyRotationManager()

def calculate_checksum(data):
    return hashlib.sha256(data).hexdigest()

try:
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(1)

    connection, client_address = server_socket.accept()

except Exception as e:
    exit(1)

try:
    while True:
        try:
            password_length_bytes = connection.recv(4)
            if not password_length_bytes:
                break

            password_length = struct.unpack('>I', password_length_bytes)[0]
            if password_length > 0:
                password_bytes = connection.recv(password_length)
                password = password_bytes.decode('utf-8', errors='replace')
                continue

            filename_length_bytes = connection.recv(4)
            if not filename_length_bytes:
                break

            filename_length = struct.unpack('>I', filename_length_bytes)[0]
            if filename_length == 0:
                break

            filename_bytes = connection.recv(filename_length)
            filename = filename_bytes.decode('utf-8', errors='replace')

            data_length_bytes = connection.recv(4)
            if not data_length_bytes:
                break
            data_length = struct.unpack('>I', data_length_bytes)[0]

            encrypted_data = bytearray()
            bytes_received = 0
            while bytes_received < data_length:
                chunk = connection.recv(min(4096, data_length - bytes_received))
                if not chunk:
                    break
                encrypted_data.extend(chunk)
                bytes_received += len(chunk)

            if bytes_received != data_length:
                break

            try:
                decrypted_data = aes_decrypt(encrypted_data, password)
            except Exception as e:
                break

            try:
                data = pickle.loads(decrypted_data)
            except Exception as e:
                break

            file_path = os.path.join(received_directory, filename)
            with open(file_path, 'wb') as received_file:
                received_file.write(data)

        except Exception as e:
            break

    input("Press Enter to close the connection...")

    try:
        connection.sendall(b'CLOSE')
    except Exception as e:
        pass

except Exception as e:
    pass
finally:
    try:
        if connection:
            connection.shutdown(socket.SHUT_RDWR)
            connection.close()
    except:
        pass

    try:
        if server_socket:
            server_socket.close()
    except:
        pass