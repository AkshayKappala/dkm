import socket
import os
import struct
import pickle
from server.decryption.aes_decryption import aes_decrypt
from shared.key_rotation_manager import KeyRotationManager

SERVER_ADDRESS = ('192.168.141.10', 12345)
received_directory = "received"
os.makedirs(received_directory, exist_ok=True)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

password = "secure_password"

key_rotation_manager = KeyRotationManager()

try:
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(1)
    print("Server listening for incoming connections...")

    connection, client_address = server_socket.accept()
    print(f"Connection established with {client_address}")

except Exception as e:
    print(f"Error establishing server socket: {e}")
    exit(1)

try:
    while True:
        try:
            print("[DEBUG] Waiting for password length...")
            password_length_bytes = connection.recv(4)
            if not password_length_bytes:
                print("[DEBUG] No password length received, closing connection.")
                break

            password_length = struct.unpack('>I', password_length_bytes)[0]
            print(f"[DEBUG] Password length received: {password_length}")
            if password_length > 0:
                password_bytes = connection.recv(password_length)
                password = password_bytes.decode('utf-8', errors='replace')
                print(f"[DEBUG] Password updated: {password}")
                continue

            print("[DEBUG] Waiting for filename length...")
            filename_length_bytes = connection.recv(4)
            if not filename_length_bytes:
                print("[DEBUG] No filename length received, closing connection.")
                break

            filename_length = struct.unpack('>I', filename_length_bytes)[0]
            print(f"[DEBUG] Filename length received: {filename_length}")
            if filename_length == 0:
                print("[DEBUG] All files received successfully.")
                break

            print("[DEBUG] Waiting for filename...")
            filename_bytes = connection.recv(filename_length)
            filename = filename_bytes.decode('utf-8', errors='replace')
            print(f"[DEBUG] Filename received: {filename}")

            print("[DEBUG] Waiting for data length...")
            data_length_bytes = connection.recv(4)
            if not data_length_bytes:
                print("[DEBUG] No data length received, closing connection.")
                break
            data_length = struct.unpack('>I', data_length_bytes)[0]
            print(f"[DEBUG] Data length received: {data_length}")

            print("[DEBUG] Receiving encrypted data...")
            encrypted_data = bytearray()
            bytes_received = 0
            while bytes_received < data_length:
                chunk = connection.recv(min(4096, data_length - bytes_received))
                if not chunk:
                    print("[DEBUG] No more data received, breaking.")
                    break
                encrypted_data.extend(chunk)
                bytes_received += len(chunk)
                print(f"[DEBUG] Received {bytes_received}/{data_length} bytes")

            if bytes_received != data_length:
                print(f"[DEBUG] Incomplete image fragment received. Expected: {data_length}, Received: {bytes_received}")
                break

            print("[DEBUG] Decrypting received data...")
            decrypted_data = aes_decrypt(encrypted_data, password)
            print(f"[DEBUG] Decrypted data size: {len(decrypted_data)} bytes")

            try:
                print("[DEBUG] Deserializing decrypted data...")
                data = pickle.loads(decrypted_data)
                print(f"[DEBUG] Deserialized data size: {len(data)} bytes")
            except Exception as e:
                print(f"[DEBUG] Error parsing decrypted data: {e}")
                break

            file_path = os.path.join(received_directory, filename)
            print(f"[DEBUG] Saving file to: {file_path}")
            with open(file_path, 'wb') as received_file:
                received_file.write(data)
            print(f"[DEBUG] File saved successfully: {file_path}")

            print(f"[DEBUG] Received and reconstructed image: {filename}")

        except Exception as e:
            print(f"[DEBUG] Error receiving image fragment: {e}")
            break

    print("[DEBUG] Image transfer complete. Waiting for user input...")
    input("Press Enter to close the connection...")

    try:
        print("[DEBUG] Sending close signal to client...")
        connection.sendall(b'CLOSE')
    except Exception as e:
        print(f"[DEBUG] Error sending close signal: {e}")

except Exception as e:
    print(f"Error during server communication: {e}")
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