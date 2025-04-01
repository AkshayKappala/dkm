import socket
import os
import struct
import pickle
import hashlib
import logging
from server.decryption.aes_decryption import aes_decrypt
from shared.key_rotation_manager import KeyRotationManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SERVER_ADDRESS = ('192.168.141.10', 12345)
received_directory = "received"
os.makedirs(received_directory, exist_ok=True)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

password = "secure_password"
key_rotation_manager = KeyRotationManager()

def calculate_checksum(data):
    return hashlib.sha256(data).hexdigest()

try:
    logging.info("Starting server at %s:%d", *SERVER_ADDRESS)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(1)
    logging.info("Server is listening for connections...")

    connection, client_address = server_socket.accept()
    logging.info("Connection established with client: %s", client_address)

except Exception as e:
    logging.error("Error starting server: %s", e)
    exit(1)

try:
    while True:
        try:
            logging.info("Waiting for incoming data...")
            password_length_bytes = connection.recv(4)
            if not password_length_bytes:
                logging.info("No password length received. Closing connection.")
                break

            password_length = struct.unpack('>I', password_length_bytes)[0]
            if password_length > 0:
                password_bytes = connection.recv(password_length)
                password = password_bytes.decode('utf-8', errors='replace')
                logging.info("Password updated by client.")
                continue

            filename_length_bytes = connection.recv(4)
            if not filename_length_bytes:
                logging.info("No filename length received. Closing connection.")
                break

            filename_length = struct.unpack('>I', filename_length_bytes)[0]
            if filename_length == 0:
                logging.info("Filename length is zero. Closing connection.")
                break

            filename_bytes = connection.recv(filename_length)
            filename = filename_bytes.decode('utf-8', errors='replace')
            logging.info("Receiving file: %s", filename)

            data_length_bytes = connection.recv(4)
            if not data_length_bytes:
                logging.info("No data length received. Closing connection.")
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
                logging.warning("Incomplete data received for file: %s", filename)
                break

            try:
                decrypted_data = aes_decrypt(encrypted_data, password)
                logging.info("File %s decrypted successfully.", filename)
            except Exception as e:
                logging.error("Error decrypting file %s: %s", filename, e)
                break

            try:
                data = pickle.loads(decrypted_data)
                if not isinstance(data, bytes):
                    raise ValueError("Invalid data format")
                logging.info("File %s deserialized successfully.", filename)
            except Exception as e:
                logging.error("Error deserializing file %s: %s", filename, e)
                continue

            file_path = os.path.join(received_directory, filename)
            with open(file_path, 'wb') as received_file:
                received_file.write(data)
                logging.info("File %s saved to %s.", filename, file_path)

        except Exception as e:
            logging.error("Error during file reception: %s", e)
            break

    input("Press Enter to close the connection...")
    logging.info("Closing connection with client.")

    try:
        connection.sendall(b'CLOSE')
    except Exception as e:
        logging.error("Error sending close message to client: %s", e)

except Exception as e:
    logging.error("Error occurred during server operation: %s", e)
finally:
    try:
        if connection:
            connection.shutdown(socket.SHUT_RDWR)
            connection.close()
            logging.info("Connection closed.")
    except Exception as e:
        logging.error("Error closing connection: %s", e)
    try:
        if server_socket:
            server_socket.close()
            logging.info("Server socket closed.")
    except Exception as e:
        logging.error("Error closing server socket: %s", e)