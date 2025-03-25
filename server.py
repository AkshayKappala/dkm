import socket
import os

# Define server address
SERVER_ADDRESS = ('192.168.141.10', 12345)

# Constant string as the KEM private/public key (for demo)
server_private_key = "server_private_key"
server_public_key = "server_public_key"

# Constant symmetric key for image encryption/decryption (for demo)
symmetric_key = "symmetric_key_123456"

# Directory to save received images
received_directory = "received"

# Ensure the received directory exists
os.makedirs(received_directory, exist_ok=True)

# Simulate decrypting the image with the symmetric key (mock operation)
def decrypt_image(encrypted_image, symmetric_key):
    decrypted_image = bytearray([b ^ ord(symmetric_key[i % len(symmetric_key)]) for i, b in enumerate(encrypted_image)])
    return decrypted_image

# Function to save the decrypted image to the received directory
def save_image(decrypted_image, filename):
    image_path = os.path.join(received_directory, filename)
    try:
        with open(image_path, 'wb') as img_file:
            img_file.write(decrypted_image)
        print(f"Image saved to {image_path}")
    except Exception as e:
        print(f"Error saving image {filename}: {e}")

# Create a socket and bind to the server address
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(1)
    print("Server listening for incoming connections...")
    
    connection, client_address = server_socket.accept()
    print(f"Connection established with {client_address}")
except Exception as e:
    print(f"Error establishing server socket: {e}")
    exit(1)

try:
    # Send the server's public key to the client
    connection.sendall(server_public_key.encode())
    
    # Receive the encapsulated symmetric key from the client
    encapsulated_key = connection.recv(1024).decode()
    
    # Simulate decapsulating the symmetric key
    if encapsulated_key == "encapsulated_symmetric_key":
        print("Symmetric key successfully received and decapsulated.")
    else:
        print("Failed to decapsulate symmetric key.")
        connection.close()
        exit(1)

    # Receive and decrypt all images
    while True:
        try:
            encrypted_image = connection.recv(4096)
            if not encrypted_image:
                break  # Exit loop when no more images are received

            # Decrypt the image using the symmetric key
            decrypted_image = decrypt_image(encrypted_image, symmetric_key)

            # Save the decrypted image to the received directory
            image_filename = f"image{len(os.listdir(received_directory)) + 1}.jpg"  # Assuming JPEG format for demo
            save_image(decrypted_image, image_filename)
        except Exception as e:
            print(f"Error receiving or decrypting image: {e}")
            break

    # Generate a new KEM key pair and send the new public key to the client
    server_public_key = "new_server_public_key"  # Mock new public key
    connection.sendall(server_public_key.encode())

except Exception as e:
    print(f"Error during server communication: {e}")
finally:
    connection.close()
    server_socket.close()
