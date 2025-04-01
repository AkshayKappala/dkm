import socket
import os
import struct
import pickle
import hashlib
import logging
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_checksum(data):
    return hashlib.sha256(data).hexdigest()

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
    
    files_to_send = sorted(read_image(sent_directory))
    if not files_to_send:
        logging.warning("No files found in the 'sent' directory to send.")
        raise Exception("No files to send")
    
    for filename in files_to_send:
        file_path = os.path.join(sent_directory, filename)
        try:
            logging.info("Processing file: %s", filename)
            should_rotate, similarity, reason = key_rotation_manager.should_rotate_key(file_path)
            logging.info("Key rotation decision for %s: %s (Reason: %s)", filename, should_rotate, reason)
            
            if should_rotate:
                password = f"{password}_{filename}"
                logging.info("Rotating key for file: %s", filename)
                password_bytes = password.encode('utf-8')
                password_length = len(password_bytes)
                client_socket.sendall(b'\x01' + struct.pack('>I', password_length) + password_bytes)

                # Wait for acknowledgment from the server after sending the new key
                ack = client_socket.recv(3)
                if ack != b"ACK":
                    logging.error("Failed to receive acknowledgment for key rotation. Aborting.")
                    break

            filename_bytes = filename.encode('utf-8')
            filename_length = len(filename_bytes)
            client_socket.sendall(b'\x02' + struct.pack('>I', filename_length) + filename_bytes)

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

    client_socket.sendall(struct.pack('>I', 0))
    logging.info("File transfer complete.")
    
    try:
        client_socket.settimeout(2.0)
        close_msg = client_socket.recv(1024)
        if close_msg == b'CLOSE':
            logging.info("Server closed the connection.")
            try:
                client_socket.sendall(b'ACK')
            except:
                pass
    except:
        logging.warning("Timeout waiting for server acknowledgment.")

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
