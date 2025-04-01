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
received_directory = "received_files"
os.makedirs(received_directory, exist_ok=True)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

encryption_key = "secure_password"
key_rotation_manager = KeyRotationManager()

def calculate_checksum(data):
    return hashlib.sha256(data).hexdigest()

def handle_client_connection(client_socket, client_address):
    global encryption_key  # Ensure the server updates the global encryption key
    logging.info("Connection established with client: %s", client_address)
    try:
        while True:
            try:
                # Receive the flag
                flag = client_socket.recv(1)
                if not flag:
                    logging.info("No flag received. Closing connection.")
                    break

                # Handle new key
                if flag == b'\x01':
                    key_length_bytes = client_socket.recv(4)
                    if not key_length_bytes:
                        logging.info("No key length received. Closing connection.")
                        break

                    key_length = int.from_bytes(key_length_bytes, 'big')
                    password_bytes = client_socket.recv(key_length)
                    encryption_key = password_bytes.decode('utf-8', errors='replace')  # Update the encryption key
                    logging.info("New key received: %s", encryption_key)

                    # Send acknowledgment for the new key
                    client_socket.sendall(b"ACK")
                    continue

                # Handle filename
                elif flag == b'\x02':
                    filename_length_bytes = client_socket.recv(4)
                    if not filename_length_bytes:
                        logging.info("No filename length received. Closing connection.")
                        break

                    filename_length = int.from_bytes(filename_length_bytes, 'big')
                    filename_bytes = client_socket.recv(filename_length)
                    filename = filename_bytes.decode('utf-8', errors='replace')

                    # Receive file data length
                    file_data_length_bytes = client_socket.recv(8)
                    if not file_data_length_bytes:
                        logging.info("No file data length received. Closing connection.")
                        break

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
                    decrypted_data = aes_decrypt(file_data, encryption_key)  # Use the updated encryption key
                    data = pickle.loads(decrypted_data)

                    # Save the file
                    save_path = os.path.join(received_directory, filename)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(data)

                    logging.info(f"File {filename} saved successfully.")
                    client_socket.sendall(b"ACK")  # Send acknowledgment to client

                # Handle end-of-transfer
                elif flag == b'\x03':
                    logging.info("End-of-transfer signal received from client.")
                    client_socket.sendall(b"ACK")  # Acknowledge end-of-transfer
                    logging.info("Acknowledgment for end-of-transfer sent to client.")
                    
                    # Wait for user input to close the connection gracefully
                    input("Press Enter to close the connection gracefully...")
                    break  # Exit the loop and close the connection

                else:
                    logging.error(f"Unknown flag received: {flag}. Closing connection.")
                    break

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
    logging.info("Server is listening for connections...")

    while True:  # Keep the server running to accept new connections
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
