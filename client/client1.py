import socket
import os
import struct
import pickle
import logging
from client.encryption.aes_encryption import aes_encrypt
from client.utils.file_utils import read_image

SERVER_ADDRESS = ('192.168.233.129', 12345)

sent_directory = "sent"
password = "secure_password"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_file_to_server(file_data, retries=3):
    for attempt in range(retries):
        try:
            client_socket.sendall(file_data)
            ack = client_socket.recv(3)
            if ack == b"ACK":
                logging.info("File sent successfully.")
                return True
            else:
                logging.warning("No acknowledgment received. Retrying...")
        except Exception as e:
            logging.error(f"Error sending file: {e}")
            if attempt < retries - 1:
                logging.info("Retrying...")
            else:
                logging.error("Max retries reached. Aborting.")
                return False

try:
    logging.info("Connecting to server at %s:%d", *SERVER_ADDRESS)
    client_socket.connect(SERVER_ADDRESS)

    # Send the encryption key
    password_bytes = password.encode('utf-8')
    password_length = len(password_bytes)
    client_socket.sendall(struct.pack('>I', password_length) + password_bytes)
    logging.info("Encryption key sent to server.")

    files_to_send = sorted(read_image(sent_directory))
    if not files_to_send:
        logging.warning("No files found in the 'sent' directory to send.")
        raise Exception("No files to send")

    for filename in files_to_send:
        file_path = os.path.join(sent_directory, filename)
        try:
            logging.info("Processing file: %s", filename)

            filename_bytes = filename.encode('utf-8')
            filename_length = len(filename_bytes)
            client_socket.sendall(struct.pack('>I', filename_length) + filename_bytes)

            with open(file_path, 'rb') as file:
                data = file.read()

            serialized_data = pickle.dumps(data)
            encrypted_data = aes_encrypt(serialized_data, password)
            logging.info("File %s encrypted successfully.", filename)

            data_length = len(encrypted_data)
            client_socket.sendall(struct.pack('>Q', data_length))  # Use 8 bytes for length
            if not send_file_to_server(encrypted_data):
                break  # Stop processing if file sending fails

        except Exception as e:
            logging.error("Error processing file %s: %s", filename, e)
            continue  # Skip to the next file

    logging.info("File transfer complete.")

except Exception as e:
    logging.error("Error occurred during client operation: %s", e)
finally:
    try:
        if client_socket:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
            logging.info("Client socket closed.")
    except:
        logging.error("Error closing client socket.")
