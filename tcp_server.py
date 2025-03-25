import socket
import threading
import logging
import signal
import sys
import time

# Configure minimal logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("server.log"), logging.StreamHandler()]
)

class TCPServer:
    def __init__(self, host='192.168.141.10', port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = {}  # Dictionary to store client connections
        self.clients_lock = threading.Lock()
        
    def start(self):
        """Start the TCP server"""
        if self.running:
            logging.warning("Server already running")
            return False
            
        try:
            # Create socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to the address
            self.server_socket.bind((self.host, self.port))
            
            # Listen for connections
            self.server_socket.listen(5)
            self.running = True
            
            logging.info(f"Server started on {self.host}:{self.port}")
            
            # Start accepting connections in a separate thread
            self.accept_thread = threading.Thread(target=self._accept_connections)
            self.accept_thread.daemon = True
            self.accept_thread.start()
            
            return True
            
        except socket.error as e:
            logging.error(f"Server startup failed: {e}")
            return False
    
    def _accept_connections(self):
        """Accept incoming connections"""
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                try:
                    client_socket, addr = self.server_socket.accept()
                    client_id = f"{addr[0]}:{addr[1]}"
                    logging.info(f"New connection from {client_id}")
                    
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
                logging.error(f"Error accepting connection: {e}")
                time.sleep(1)
    
    def _handle_client(self, client_socket, client_id):
        """Monitor client connection for disconnects"""
        try:
            # Keep socket open and check for disconnection
            while self.running:
                try:
                    # Just peek at the socket to see if it's still connected
                    client_socket.settimeout(1.0)
                    data = client_socket.recv(16, socket.MSG_PEEK)
                    if not data and client_socket.fileno() != -1:
                        logging.info(f"Client {client_id} disconnected")
                        break
                    time.sleep(0.5)  # Reduce CPU usage
                except socket.timeout:
                    continue
                except socket.error as e:
                    if self.running:
                        logging.error(f"Error with client {client_id}: {e}")
                    break
        finally:
            self._remove_client(client_id)
    
    def _remove_client(self, client_id):
        """Remove a client from the clients dictionary"""
        with self.clients_lock:
            if client_id in self.clients:
                try:
                    self.clients[client_id].close()
                except:
                    pass
                del self.clients[client_id]
                logging.info(f"Removed client {client_id}")
    
    def send_to_client(self, client_id, data):
        """Send binary data to a specific client
        
        Args:
            client_id: Client identifier (IP:port)
            data: Binary data to send
            
        Returns:
            bool: Success status
        """
        with self.clients_lock:
            if client_id in self.clients:
                try:
                    # Send data length as 4-byte integer first
                    data_length = len(data).to_bytes(4, byteorder='big')
                    self.clients[client_id].sendall(data_length)
                    
                    # Send actual data
                    self.clients[client_id].sendall(data)
                    logging.debug(f"Sent {len(data)} bytes to {client_id}")
                    return True
                except socket.error as e:
                    logging.error(f"Failed to send to {client_id}: {e}")
                    self._remove_client(client_id)
            else:
                logging.warning(f"Client {client_id} not found")
            return False
    
    def broadcast(self, data):
        """Send binary data to all connected clients
        
        Args:
            data: Binary data to send
            
        Returns:
            int: Number of clients that received the data
        """
        count = 0
        with self.clients_lock:
            client_ids = list(self.clients.keys())
            
        for client_id in client_ids:
            if self.send_to_client(client_id, data):
                count += 1
                
        return count
    
    def get_client_list(self):
        """Get a list of connected client IDs
        
        Returns:
            list: List of client ID strings
        """
        with self.clients_lock:
            return list(self.clients.keys())
    
    def stop(self):
        """Stop the server"""
        if not self.running:
            return
            
        logging.info("Shutting down server...")
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
            
        logging.info("Server stopped")

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    if server:
        server.stop()
    sys.exit(0)

# Create a singleton server instance
server = None

def get_server(host='192.168.141.10', port=5555):
    """Get or create the server instance"""
    global server
    if server is None:
        server = TCPServer(host, port)
    return server

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server = get_server()
    server.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()