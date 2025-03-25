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
    print("Received server public key")

    encapsulated_key = b"encapsulated_symmetric_key"  # Mock, send as bytes
    
    # Send the key length first
    key_length = len(encapsulated_key)
    client_socket.sendall(struct.pack('>I', key_length))
    
    # Send the key
    client_socket.sendall(encapsulated_key)
    print(f"Sent encapsulated key: {encapsulated_key}")
    
    # Wait for initial server ready signal
    response = client_socket.recv(5)  # "READY" is 5 bytes
    if response != b"READY":
        print("Server not ready to receive files, aborting.")
        raise Exception("Server not ready")

    # Get all files and sort them by name
    files_to_send = []
    for filename in os.listdir(sent_directory):
        file_path = os.path.join(sent_directory, filename)
        if os.path.isfile(file_path):
            files_to_send.append(filename)
    
    # Sort files alphabetically
    files_to_send.sort()
    
    # Iterate over files in sorted order
    for filename in files_to_send:
        file_path = os.path.join(sent_directory, filename)
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
            
            # Wait for server confirmation before sending next file
            response = client_socket.recv(5)  # "READY" is 5 bytes
            if response != b"READY":
                print("Server not ready for next file, aborting.")
                break

        except Exception as e:
            print(f"Error sending file {filename}: {e}")
            break

    # Signal the end of the files with a data length of 0
    client_socket.sendall(struct.pack('>I', 0))

    server_public_key_pem = client_socket.recv(1024).decode()
    print("Received new server public key")
    
    # Wait for user input before closing connection
    input("File transfer complete. Press Enter to close the connection...")
    
    # We can optionally try to receive any closing message from the server
    try:
        client_socket.settimeout(2.0)
        client_socket.recv(1024)
    except:
        pass  # No need to log anything here

except Exception as e:
    print(f"Error during client communication: {e}")
finally:
    client_socket.close()
    print("Connection closed.")
