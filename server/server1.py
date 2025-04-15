import socket
import os
import struct
import pickle
import logging
from server.decryption.aes_decryption import aes_decrypt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SERVER_ADDRESS = ('192.168.233.129', 12345)
received_directory = "received_files"
os.makedirs(received_directory, exist_ok=True)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

encryption_key = None  # Key will be received once at the beginning

def handle_client_connection(client_socket, client_address):
    global encryption_key
    logging.info("Connection established with client: %s", client_address)
    try:
        # Receive the encryption key
        key_length_bytes = client_socket.recv(4)
        key_length = int.from_bytes(key_length_bytes, 'big')
        encryption_key = client_socket.recv(key_length).decode('utf-8')
        logging.info("Encryption key received: %s", encryption_key)

        while True:
            try:
                # Receive filename
                filename_length_bytes = client_socket.recv(4)
                if not filename_length_bytes:
                    logging.info("No filename length received. Closing connection.")
                    break

                filename_length = int.from_bytes(filename_length_bytes, 'big')
                filename_bytes = client_socket.recv(filename_length)
                filename = filename_bytes.decode('utf-8', errors='replace')

                # Receive file data length
                file_data_length_bytes = client_socket.recv(8)
                file_data_length = int.from_bytes(file_data_length_bytes, 'big')
                file_data = bytearray()
                bytes_received = 0
                while bytes_received < file_data_length:
                    chunk = client_socket.recv(min(4096, file_data_length - bytes_received))
                    if not chunk:
                        raise ConnectionError("Incomplete data received.")
                    file_data.extend(chunk)
                    bytes_received += len(chunk)

                # Decrypt and deserialize the file
                decrypted_data = aes_decrypt(file_data, encryption_key)
                data = pickle.loads(decrypted_data)

                # Save the file
                save_path = os.path.join(received_directory, filename)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(data)

                logging.info(f"File {filename} saved successfully.")
                client_socket.sendall(b"ACK")  # Send acknowledgment to client

            except ConnectionError as e:
                logging.warning(f"Connection error: {e}")
                break
            except Exception as e:
                logging.error(f"Error handling client data: {e}")
                break
    finally:
        try:
            client_socket.close()
            logging.info("Client connection closed.")
        except Exception as e:
            logging.error(f"Error closing client socket: {e}")

try:
    logging.info("Starting server at %s:%d", *SERVER_ADDRESS)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(1)
    logging.info("Server is listening for a connection...")

    connection, client_address = server_socket.accept()
    handle_client_connection(connection, client_address)

except Exception as e:
    logging.error("Error starting server: %s", e)
    exit(1)

finally:
    try:
        if server_socket:
            server_socket.close()
            logging.info("Server socket closed.")
    except Exception as e:
        logging.error("Error closing server socket: %s", e)
