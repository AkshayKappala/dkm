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

# Increase socket buffer size
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # Set send buffer size to 64KB
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # Set receive buffer size to 64KB
client_socket.settimeout(5)  # Set a 5-second timeout for socket operations

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_file_to_server(file_data, retries=3):
    for attempt in range(retries):
        try:
            total_sent = 0
            while total_sent < len(file_data):
                sent = client_socket.send(file_data[total_sent:total_sent + 65536])  # Match buffer size
                if sent == 0:
                    raise RuntimeError("Socket connection broken")
                total_sent += sent
            ack = client_socket.recv(3)
            if ack == b"ACK":
                logging.info("Acknowledgment received for file.")
                return True
            else:
                logging.warning("Unexpected acknowledgment received. Retrying...")
        except socket.timeout:
            logging.error("Timeout occurred while sending file. Retrying...")
        except Exception as e:
            logging.error(f"Error sending file: {e}")
        logging.warning("Retrying file transfer (Attempt %d/%d)...", attempt + 1, retries)
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
                logging.error("Failed to send file %s after retries. Skipping...", filename)
                continue

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
    except Exception as e:
        logging.error("Error closing client socket: %s", e)