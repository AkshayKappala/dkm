import socket
import os
import struct
from client.encryption.aes_encryption import aes_encrypt
from client.encryption.dwt_processor import process_image
from shared.crypto_utils import derive_key, sha256_hash, sha512_hash
from shared.key_rotation_manager import KeyRotationManager
from client.utils.file_utils import read_image  # Import read_image from file_utils

SERVER_ADDRESS = ('192.168.141.10', 12345)

# Directory containing files to send
sent_directory = "sent"

# Create a key rotation manager
key_rotation_manager = KeyRotationManager()

# Password for encryption
password = "secure_password"  # In a real app, this would be securely provided

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    print(f"Connecting to server at {SERVER_ADDRESS}...")
    client_socket.connect(SERVER_ADDRESS)
    print("Connected to server successfully")
    
    # Get all image files to send
    files_to_send = read_image(sent_directory)  # Use read_image from file_utils
    if not files_to_send:
        print(f"No valid image files found in directory: {sent_directory}")
        raise Exception("No files to send")
    
    # Iterate over files in sorted order
    for filename in files_to_send:
        file_path = os.path.join(sent_directory, filename)
        try:
            print(f"Processing file: {filename}")
            
            # Check if we should rotate the key for this file
            should_rotate, similarity, reason = key_rotation_manager.should_rotate_key(file_path)
            if should_rotate:
                print(f"Key rotation triggered: {reason}")
                # In a real implementation, you would rotate the key here
                # For now, we'll just update the password for demonstration
                password = f"{password}_{filename}"
                print(f"Key rotated. New key derived from updated password.")
            
            # Send the filename length
            filename_bytes = filename.encode()
            filename_length = len(filename_bytes)
            client_socket.sendall(struct.pack('>I', filename_length))
            
            # Send the filename
            client_socket.sendall(filename_bytes)
            
            with open(file_path, 'rb') as file:
                data = file.read()
                
            # Encrypt the data
            encrypted_data = aes_encrypt(data, password)
            
            # Send the data length
            data_length = len(encrypted_data)
            client_socket.sendall(struct.pack('>I', data_length))
            
            # Send the encrypted data
            client_socket.sendall(encrypted_data)
            
            print(f"Sent encrypted file: {filename}")

        except Exception as e:
            print(f"Error sending file {filename}: {e}")
            break

    # Signal the end of files with a filename length of 0
    client_socket.sendall(struct.pack('>I', 0))
    print("Signaled end of file transmission")
    
    # Wait for user input before closing connection
    input("File transfer complete. Press Enter to close the connection...")
    
    # We can optionally try to receive any closing message from the server
    print("Closing connection...")
    try:
        client_socket.settimeout(2.0)
        close_msg = client_socket.recv(1024)
        if close_msg == b'CLOSE':
            print("Received close signal from server")
            # Optionally send acknowledgment
            try:
                client_socket.sendall(b'ACK')
            except:
                pass  # It's okay if this fails
    except:
        pass  # No need to log anything here

except Exception as e:
    print(f"Error during client communication: {e}")
finally:
    # Ensure proper socket cleanup
    try:
        if client_socket:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
            print("Connection closed.")
    except:
        pass  # Socket might already be closed