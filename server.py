import socket
import os
import struct

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
    server_public_key = "server_public_key" # Mock
    connection.sendall(server_public_key.encode())

    encapsulated_key = connection.recv(1024).decode()
    if encapsulated_key == "encapsulated_symmetric_key": # Mock
        print("Symmetric key successfully received and decapsulated.")
    else:
        print("Failed to decapsulate symmetric key.")
        connection.close()
        exit(1)

    # Receive files
    while True:
        try:
            # Receive the filename length
            filename_length_bytes = connection.recv(4)
            if not filename_length_bytes:
                print("Client disconnected.")
                break  # Connection closed

            filename_length = struct.unpack('>I', filename_length_bytes)[0]
            print(f"Filename length: {filename_length}")

            if filename_length == 0:
                print("End of files signal received.")
                break  # End of files

            # Receive the filename
            filename_bytes = connection.recv(filename_length)
            filename = filename_bytes.decode()
            print(f"Filename: {filename}")

            # Receive the data length
            data_length_bytes = connection.recv(4)
            if not data_length_bytes:
                print("Client disconnected while expecting data length.")
                break
            data_length = struct.unpack('>I', data_length_bytes)[0]
            print(f"Data length: {data_length}")

            # Receive the data
            received_data = bytearray()
            bytes_received = 0
            while bytes_received < data_length:
                chunk = connection.recv(min(4096, data_length - bytes_received))
                if not chunk:
                    print("Client disconnected during data transmission.")
                    break
                received_data.extend(chunk)
                bytes_received += len(chunk)

            if bytes_received != data_length:
                print("Incomplete file received.")
                break

            # Save the received data to a file
            try:
                file_path = os.path.join(received_directory, filename)
                with open(file_path, 'wb') as received_file:
                    received_file.write(received_data)

                print(f"Received and saved file: {filename}")
            except Exception as e:
                print(f"Error saving file {filename}: {e}")
                break # Stop if saving fails

        except Exception as e:
            print(f"General error receiving file: {e}")
            break

    new_server_public_key = "new_server_public_key" # Mock
    connection.sendall(new_server_public_key.encode())

except Exception as e:
    print(f"Error during server communication: {e}")
finally:
    connection.close()
    server_socket.close()
