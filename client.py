import socket
import os

# Define server address
SERVER_ADDRESS = ('192.168.141.10', 12345)

# Constant string as the KEM public key (for demo)
server_public_key = "server_public_key"

# Constant symmetric key for image encryption/decryption (for demo)
symmetric_key = "symmetric_key_123456"

# Simulate encrypting the image with the symmetric key (mock operation)
def encrypt_image(image_data, symmetric_key):
    encrypted_image = bytearray([b ^ ord(symmetric_key[i % len(symmetric_key)]) for i, b in enumerate(image_data)])
    return encrypted_image

# Simulate encapsulating the symmetric key (mock operation)
def encapsulate_symmetric_key(symmetric_key, server_public_key):
    if server_public_key == "server_public_key":
        return "encapsulated_symmetric_key"  # Mock encapsulation
    else:
        return ""

# Directory containing images
image_directory = "images"  # Change this to your directory with images

# Create a socket and connect to the server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect(SERVER_ADDRESS)
    
    # Receive the server's public key
    server_public_key_pem = client_socket.recv(1024).decode()
    print(f"Received server public key: {server_public_key_pem}")
    
    # Generate a symmetric key (for demo, we use the constant one)
    symmetric_key = "symmetric_key_123456"
    
    # Encapsulate the symmetric key using the server's public key
    encapsulated_key = encapsulate_symmetric_key(symmetric_key, server_public_key)
    
    # Send the encapsulated key to the server
    client_socket.sendall(encapsulated_key.encode())

    # Iterate over the images in the directory and send each one
    for filename in os.listdir(image_directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):  # Process image files only
            file_path = os.path.join(image_directory, filename)
            
            try:
                with open(file_path, 'rb') as img_file:
                    image_data = img_file.read()
            
                # Encrypt the image using the symmetric key
                encrypted_image = encrypt_image(image_data, symmetric_key)

                # Send the encrypted image to the server
                client_socket.sendall(encrypted_image)
                print(f"Sent encrypted image: {filename}")
            except Exception as e:
                print(f"Error reading or sending image {filename}: {e}")

    # Signal the end of the images
    client_socket.sendall(b'')  # Send an empty message to indicate no more images

    # Receive the new public key from the server for key update
    server_public_key_pem = client_socket.recv(1024).decode()
    print(f"Received new server public key: {server_public_key_pem}")

except Exception as e:
    print(f"Error during client communication: {e}")
finally:
    client_socket.close()
