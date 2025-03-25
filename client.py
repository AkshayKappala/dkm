import socket
import os
import struct

SERVER_ADDRESS = ('192.168.141.10', 12345)

# Directory containing files to send
sent_directory = "sent"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect(SERVER_ADDRESS)
    server_public_key_pem = client_socket.recv(1024).decode()
    print(f"Received server public key: {server_public_key_pem}")

    encapsulated_key = b"encapsulated_symmetric_key"  # Mock, send as bytes
    
    # Send the key length first
    key_length = len(encapsulated_key)
    client_socket.sendall(struct.pack('>I', key_length))
    
    # Send the key
    client_socket.sendall(encapsulated_key)
    print(f"Sent encapsulated key: {encapsulated_key}")

    # Iterate over files in the sent directory
    for filename in os.listdir(sent_directory):
        file_path = os.path.join(sent_directory, filename)

        # Check if it's a file (not a subdirectory)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'rb') as file_to_send:
                    data = file_to_send.read()

                # Prepend the filename and its length
                filename_bytes = filename.encode()
                filename_length = len(filename_bytes)

                # Prepend the length of the filename
                client_socket.sendall(struct.pack('>I', filename_length))
                # Send the filename
                client_socket.sendall(filename_bytes)

                # Prepend the length of the data
                data_length = len(data)
                client_socket.sendall(struct.pack('>I', data_length))
                # Send the data
                client_socket.sendall(data)

                print(f"Sent file: {filename}")

            except Exception as e:
                print(f"Error reading or sending file {filename}: {e}")

    # Signal the end of the files with a data length of 0
    client_socket.sendall(struct.pack('>I', 0))

    server_public_key_pem = client_socket.recv(1024).decode()
    print(f"Received new server public key: {server_public_key_pem}")

except Exception as e:
    print(f"Error during client communication: {e}")
finally:
    client_socket.close()
