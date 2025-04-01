import socket
import os
import struct
from dkm.client.encryption.aes_encryption import aes_encrypt
from dkm.client.encryption.dwt_processor import process_image
from dkm.shared.crypto_utils import derive_key, sha256_hash, sha512_hash
from dkm.client.utils.file_utils import read_image

SERVER_ADDRESS = ('192.168.141.10', 12345)

# Directory containing files to send
sent_directory = "sent"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect(SERVER_ADDRESS)
    server_public_key_pem = client_socket.recv(1024).decode()
    print(f"Received server public key: {server_public_key_pem}")
    
    key_counter = 1  # Initialize key counter

    encapsulated_key = f"encapsulated_symmetric_key_{key_counter}".encode()  # Mock with counter
    
    # Send the key length first
    key_length = len(encapsulated_key)
    client_socket.sendall(struct.pack('>I', key_length))
    
    # Send the key
    client_socket.sendall(encapsulated_key)
    print(f"Sent encapsulated key {key_counter}: {encapsulated_key}")
    
    # Wait for initial server ready signal
    response = client_socket.recv(5)  # "READY" is 5 bytes
    if response != b"READY":
        print("Server not ready to receive files, aborting.")
        raise Exception("Server not ready")

    # Get all image files to send
    files_to_send = read_image(sent_directory)
    
    # Iterate over files in sorted order
    for filename in files_to_send:
        file_path = os.path.join(sent_directory, filename)
        try:
            # Process the image to get encrypted fragments
            fragments = process_image(file_path)
            for fragment in fragments:
                encrypted_fragment = aes_encrypt(fragment)  # Updated function call
                
                # Prepend the length of the encrypted fragment
                fragment_length = len(encrypted_fragment)
                client_socket.sendall(struct.pack('>I', fragment_length))
                client_socket.sendall(encrypted_fragment)

                print(f"Sent encrypted fragment of file: {filename}")
                
                # Wait for server response - could be READY or NEWKEY
                response = client_socket.recv(6)  # "NEWKEY" is 6 bytes, "READY" is 5 bytes
                
                if response == b"NEWKEY":
                    key_counter += 1  # Increment key counter
                    print(f"Received request for key rotation #{key_counter}")
                    # Receive new public key
                    new_public_key = client_socket.recv(1024).decode()
                    print(f"Received new public key {key_counter}: {new_public_key}")
                    
                    # Generate and send new encapsulated key
                    new_encapsulated_key = f"encapsulated_symmetric_key_{key_counter}".encode()  # Mock with counter
                    
                    # Send new key length
                    new_key_length = len(new_encapsulated_key)
                    client_socket.sendall(struct.pack('>I', new_key_length))
                    
                    # Send new encapsulated key
                    client_socket.sendall(new_encapsulated_key)
                    print(f"Sent encapsulated key {key_counter}: {new_encapsulated_key}")
                    
                    # Wait for ready signal after key rotation
                    ready_response = client_socket.recv(5)
                    if ready_response != b"READY":
                        print("Server not ready after key rotation, aborting.")
                        break
                    
                elif response == b"READY":
                    # Server is ready for next fragment, continue
                    pass
                else:
                    print(f"Unexpected response from server: {response}, aborting.")
                    break

        except Exception as e:
            print(f"Error sending file {filename}: {e}")
            break

    # Signal the end of the fragments with a data length of 0
    client_socket.sendall(struct.pack('>I', 0))

    server_public_key_pem = client_socket.recv(1024).decode()
    print(f"Received final server public key: {server_public_key_pem}")
    
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

# Example usage of process_image
# image_path = "path/to/image.png"
# fragments = process_image(image_path)