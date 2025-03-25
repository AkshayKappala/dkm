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
    key_counter = 1  # Initialize key counter
    server_public_key = f"server_public_key_{key_counter}"  # Mock
    connection.sendall(server_public_key.encode())

    # Receive the key length first
    key_length_bytes = connection.recv(4)
    key_length = struct.unpack('>I', key_length_bytes)[0]
    
    # Receive the key with the exact length
    encapsulated_key = connection.recv(key_length)
    print(f"Received encapsulated key: {encapsulated_key}")

    # Update check to match client's new key format with counter
    expected_key = f"encapsulated_symmetric_key_{key_counter}".encode()
    if encapsulated_key == expected_key:
        print("Symmetric key successfully received.")
        # Send initial ready signal to the client
        connection.sendall(b"READY")
    else:
        print("Failed to receive symmetric key.")
        print(f"Expected: {expected_key}, Received: {encapsulated_key}")
        connection.close()
        exit(1)

    # Receive files
    files_received = 0  # Counter to track received files
    key_rotation_threshold = 3  # Change keys after every 3 files (configurable)
    
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

            # Receive the data
            received_data = bytearray()
            bytes_received = 0
            while bytes_received < data_length:
                chunk = connection.recv(min(4096, data_length - bytes_received))
                if not chunk:
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

                print(f"Received file: {filename}")
                files_received += 1
                
                # Check if we need to rotate keys
                if files_received % key_rotation_threshold == 0:
                    key_counter += 1  # Increment key counter
                    # Generate and send new key
                    new_server_public_key = f"server_public_key_{key_counter}"  # Mock with counter
                    print(f"Rotating keys after {files_received} files - New key: {new_server_public_key}")
                    # Send key rotation signal
                    connection.sendall(b"NEWKEY")
                    # Send the new key
                    connection.sendall(new_server_public_key.encode())
                    
                    # Wait for client to acknowledge and send new encapsulated key
                    key_length_bytes = connection.recv(4)
                    key_length = struct.unpack('>I', key_length_bytes)[0]
                    
                    # Receive the new encapsulated key
                    new_encapsulated_key = connection.recv(key_length)
                    print(f"Received encapsulated key {key_counter}: {new_encapsulated_key}")
                    
                    # Send ready signal after key rotation is complete
                    connection.sendall(b"READY")
                else:
                    # Send regular ready signal for next file
                    connection.sendall(b"READY")
                
            except Exception as e:
                print(f"Error saving file {filename}: {e}")
                break  # Stop if saving fails

        except Exception as e:
            print(f"Error receiving file: {e}")
            break

    # When all files are sent, send the final key update
    key_counter += 1  # Increment for final key
    final_server_public_key = f"server_public_key_{key_counter}"  # Mock with counter
    print(f"Sending final key: {final_server_public_key}")
    connection.sendall(final_server_public_key.encode())
    
    # Wait for user input before closing connection
    input("File transfer complete. Press Enter to close the connection...")
    
    # Send a termination signal to client
    print("Closing connection...")
    try:
        connection.sendall(b'CLOSE')
        # Give the client time to process and close
        connection.settimeout(3.0)
        try:
            # Try to receive any final acknowledgment
            connection.recv(1024)
        except socket.timeout:
            pass  # It's okay if we don't receive anything
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
