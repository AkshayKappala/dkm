#!/usr/bin/env python
import os
import sys
import socket
import threading
import logging
import signal
import time
import json
import struct
from tcp_client import get_client  # Use your existing TCP client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("ipc_server.log"), logging.StreamHandler()]
)
logger = logging.getLogger("ipc_server")

class IPCServer:
    def __init__(self, socket_path="/tmp/dkm_ipc.sock", tcp_host='192.168.141.10', tcp_port=5555):
        """
        Initialize the IPC server that serves as a bridge between local processes and the TCP connection
        
        Args:
            socket_path: Path to the Unix domain socket
            tcp_host: TCP server host to connect to
            tcp_port: TCP server port to connect to
        """
        self.socket_path = socket_path
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.server_socket = None
        self.running = False
        self.clients = {}  # Store client connections
        self.clients_lock = threading.Lock()
        self.tcp_client = None
        
    def start(self):
        """Start the IPC server"""
        if self.running:
            logger.warning("IPC Server already running")
            return False
            
        try:
            # Remove socket file if it exists
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
            
            # Create socket
            self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            
            # Bind to the socket path
            self.server_socket.bind(self.socket_path)
            
            # Listen for connections
            self.server_socket.listen(5)
            self.running = True
            
            # Set proper permissions for socket file
            os.chmod(self.socket_path, 0o777)  # Everyone can read/write
            
            logger.info(f"IPC Server started on {self.socket_path}")
            
            # Connect to the TCP server
            self._connect_to_tcp_server()
            
            # Start accepting connections in a separate thread
            self.accept_thread = threading.Thread(target=self._accept_connections)
            self.accept_thread.daemon = True
            self.accept_thread.start()
            
            return True
            
        except socket.error as e:
            logger.error(f"IPC Server startup failed: {e}")
            if self.server_socket:
                self.server_socket.close()
            return False
            
    def _connect_to_tcp_server(self):
        """Connect to the TCP server"""
        try:
            # Use existing TCP client infrastructure
            self.tcp_client = get_client(self.tcp_host, self.tcp_port)
            
            # Try to connect if not already connected
            if not self.tcp_client.is_connected():
                if self.tcp_client.connect():
                    logger.info(f"Connected to TCP server at {self.tcp_host}:{self.tcp_port}")
                    return True
                else:
                    logger.error("Failed to connect to TCP server")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error connecting to TCP server: {e}")
            return False
            
    def _accept_connections(self):
        """Accept incoming connections from local processes"""
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                try:
                    client_socket, _ = self.server_socket.accept()
                    client_id = id(client_socket)
                    
                    # Start a thread for this client
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_id)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    # Add client to dictionary
                    with self.clients_lock:
                        self.clients[client_id] = client_socket
                        
                except socket.timeout:
                    continue
                    
            except socket.error as e:
                if not self.running:
                    break
                logger.error(f"Error accepting connection: {e}")
                time.sleep(1)
        
        logger.debug("Accept thread terminated")
    
    def _handle_client(self, client_socket, client_id):
        """Handle a client connection"""
        try:
            while self.running:
                try:
                    # First receive the message header (8 bytes for message length)
                    client_socket.settimeout(1.0)
                    header = client_socket.recv(8)
                    
                    if not header:
                        logger.info(f"Client {client_id} disconnected")
                        break
                        
                    # Parse header to get message length
                    msg_len = struct.unpack("!Q", header)[0]
                    
                    # Receive the message data
                    data = b""
                    bytes_received = 0
                    
                    while bytes_received < msg_len:
                        chunk = client_socket.recv(min(4096, msg_len - bytes_received))
                        if not chunk:
                            break
                        data += chunk
                        bytes_received += len(chunk)
                    
                    if bytes_received < msg_len:
                        logger.warning(f"Incomplete message from client {client_id}")
                        break
                    
                    # Process the received data
                    await_response = self._process_client_message(data, client_socket)
                    
                    if not await_response:
                        # If we're not waiting for a response, send an ACK
                        ack = {"status": "ok"}
                        self._send_response(client_socket, json.dumps(ack).encode())
                        
                except socket.timeout:
                    continue
                except socket.error as e:
                    logger.error(f"Socket error with client {client_id}: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error handling client {client_id}: {e}")
                    # Send error response
                    try:
                        error_msg = {"status": "error", "message": str(e)}
                        self._send_response(client_socket, json.dumps(error_msg).encode())
                    except:
                        pass
                    break
                
        finally:
            self._remove_client(client_id)
    
    def _process_client_message(self, data, client_socket):
        """
        Process a message from a client
        
        Returns:
            bool: True if we're waiting for a response to send back to the client
        """
        try:
            # Try to interpret as JSON first (for control messages)
            try:
                msg = json.loads(data)
                
                # Handle different message types
                if msg.get("type") == "connect":
                    # Request to ensure TCP connection is established
                    if not self._connect_to_tcp_server():
                        error_msg = {"status": "error", "message": "Failed to connect to TCP server"}
                        self._send_response(client_socket, json.dumps(error_msg).encode())
                    else:
                        success_msg = {"status": "ok", "connected": True}
                        self._send_response(client_socket, json.dumps(success_msg).encode())
                    return True
                    
                elif msg.get("type") == "status":
                    # Return TCP connection status
                    connected = self.tcp_client and self.tcp_client.is_connected()
                    status_msg = {"status": "ok", "connected": connected}
                    self._send_response(client_socket, json.dumps(status_msg).encode())
                    return True
                    
                # Add more control message types as needed
                
            except json.JSONDecodeError:
                # Not JSON, treat as binary data to forward
                pass
                
            # Forward binary data to the TCP server
            if self.tcp_client and self.tcp_client.is_connected():
                success = self.tcp_client.send(data)
                if not success:
                    error_msg = {"status": "error", "message": "Failed to send data to TCP server"}
                    self._send_response(client_socket, json.dumps(error_msg).encode())
                    return True
            else:
                error_msg = {"status": "error", "message": "Not connected to TCP server"}
                self._send_response(client_socket, json.dumps(error_msg).encode())
                return True
                
            return False  # No specific response needed, just acknowledge
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_msg = {"status": "error", "message": str(e)}
            self._send_response(client_socket, json.dumps(error_msg).encode())
            return True
    
    def _send_response(self, client_socket, data):
        """Send a response to a client"""
        try:
            # Send header with message length
            header = struct.pack("!Q", len(data))
            client_socket.sendall(header + data)
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    def _remove_client(self, client_id):
        """Remove a client from the clients dictionary"""
        with self.clients_lock:
            if client_id in self.clients:
                try:
                    self.clients[client_id].close()
                except:
                    pass
                del self.clients[client_id]
                logger.debug(f"Removed client {client_id}")
    
    def stop(self):
        """Stop the IPC server"""
        if not self.running:
            return
            
        logger.info("Shutting down IPC server...")
        self.running = False
        
        # Close all client connections
        with self.clients_lock:
            for client_socket in self.clients.values():
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            
        # Clean up socket file
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
            
        logger.info("IPC server stopped")

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    if ipc_server:
        ipc_server.stop()
    sys.exit(0)

# Create a singleton server instance
ipc_server = None

def get_ipc_server(socket_path="/tmp/dkm_ipc.sock", tcp_host='192.168.141.10', tcp_port=5555):
    """Get or create the IPC server instance"""
    global ipc_server
    if ipc_server is None:
        ipc_server = IPCServer(socket_path, tcp_host, tcp_port)
    return ipc_server

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    ipc_server = get_ipc_server()
    ipc_server.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ipc_server.stop()