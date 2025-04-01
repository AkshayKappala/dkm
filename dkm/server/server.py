import socket
import os
import struct
from decryption.aes_decryption import decrypt_image_fragment
from decryption.dwt_reconstructor import reconstruct_image
from shared.crypto_utils import generate_sha256_hash

SERVER_ADDRESS = ('192.168.141.10', 12345)
received_directory = "received"
os.makedirs(received_directory, exist_ok=True)

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
    while True:
        try:
            # Receive the filename length
            filename_length_bytes = connection.recv(4)
            if not filename_length_bytes:
                break  # Connection closed

            filename_length = struct.unpack('>I', filename_length_bytes)[0]

            if filename_length == 0:
                print("All files received successfully.")
                break  # End of files

            # Receive the filename
            filename_bytes = connection.recv(filename_length)
            filename = filename_bytes.decode()

            # Receive the data length
            data_length_bytes = connection.recv(4)
            if not data_length_bytes:
                break
            data_length = struct.unpack('>I', data_length_bytes)[0]

            # Receive the encrypted image fragment
            encrypted_data = bytearray()
            bytes_received = 0
            while bytes_received < data_length:
                chunk = connection.recv(min(4096, data_length - bytes_received))
                if not chunk:
                    break
                encrypted_data.extend(chunk)
                bytes_received += len(chunk)

            if bytes_received != data_length:
                print("Incomplete image fragment received.")
                break

            # Decrypt the received image fragment
            decrypted_data = decrypt_image_fragment(encrypted_data)

            # Reconstruct the image from the decrypted fragments
            reconstructed_image = reconstruct_image(decrypted_data)

            # Save the reconstructed image
            file_path = os.path.join(received_directory, filename)
            with open(file_path, 'wb') as received_file:
                received_file.write(reconstructed_image)

            print(f"Received and reconstructed image: {filename}")

        except Exception as e:
            print(f"Error receiving image fragment: {e}")
            break

    # Wait for user input before closing connection
    input("Image transfer complete. Press Enter to close the connection...")

    # Send a termination signal to client
    print("Closing connection...")
    try:
        connection.sendall(b'CLOSE')
    except:
        print("Client may have already disconnected")

except Exception as e:
    print(f"Error during server communication: {e}")
finally:
    # Ensure proper socket cleanup
    try:
        if connection:
            connection.shutdown(socket.SHUT_RDWR)
            connection.close()
            print("Connection closed.")
    except:
        pass  # Connection might already be closed

    try:
        if server_socket:
            server_socket.close()
            print("Server socket closed.")
    except:
        pass  # Socket might already be closed