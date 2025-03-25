import socket
import threading
import logging
import time
import sys
import signal

# Configure minimal logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("client.log"), logging.StreamHandler()]
)

class TCPClient:
    def __init__(self, server_host='192.168.141.10', server_port=5555, client_ip='192.168.232.10'):
        self.server_host = server_host
        self.server_port = server_port
        self.client_ip = client_ip
        self.socket = None
        self.connected = False
        self.running = False
        self.receive_thread = None
        self.receive_callback = None  # Callback for received data
        
    def connect(self, timeout=5):
        """Connect to the server
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            bool: Success status
        """
        if self.connected:
            logging.warning("Already connected to server")
            return True
            
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Bind to specific client IP if provided
            if self.client_ip:
                try:
                    self.socket.bind((self.client_ip, 0))  # 0 means random port
                except socket.error as e:
                    logging.warning(f"Could not bind to client IP {self.client_ip}: {e}")
            
            # Set timeout for connection attempt
            self.socket.settimeout(timeout)
            
            # Connect to server
            logging.info(f"Connecting to server at {self.server_host}:{self.server_port}...")
            self.socket.connect((self.server_host, self.server_port))
            
            self.connected = True
            self.running = True
            
            # Start receive thread if a callback is set
            if self.receive_callback:
                self._start_receive_thread()
            
            logging.info(f"Connected to server at {self.server_host}:{self.server_port}")
            return True
            
        except socket.error as e:
            logging.error(f"Failed to connect: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def set_receive_callback(self, callback):
        """Set callback function for received data
        
        The callback function should accept two parameters:
        1. client: The TCPClient instance
        2. data: The received binary data
        
        Args:
            callback: Function to call when data is received
        """
        self.receive_callback = callback
        
        # Start receive thread if we're already connected
        if self.connected and not self.receive_thread:
            self._start_receive_thread()
    
    def _start_receive_thread(self):
        """Start the receive thread"""
        self.receive_thread = threading.Thread(target=self._receive_data)
        self.receive_thread.daemon = True
        self.receive_thread.start()
    
    def _receive_data(self):
        """Continuously receive data from the server"""
        while self.running and self.socket:
            try:
                # First, receive the data length (4 bytes)
                self.socket.settimeout(1.0)
                
                try:
                    length_bytes = self._receive_exact(4)
                    if not length_bytes:
                        break
                    
                    data_length = int.from_bytes(length_bytes, byteorder='big')
                    
                    # Receive the actual data
                    data = self._receive_exact(data_length)
                    if not data:
                        break
                    
                    logging.debug(f"Received {len(data)} bytes")
                    
                    # Call the callback function with the received data
                    if self.receive_callback:
                        try:
                            self.receive_callback(self, data)
                        except Exception as e:
                            logging.error(f"Error in receive callback: {e}")
                            
                except socket.timeout:
                    # Just a timeout to check if we're still running
                    continue
            except socket.error as e:
                if self.running:
                    logging.error(f"Connection error: {e}")
                self.disconnect()
                break
        
        logging.debug("Receive thread terminated")
    
    def _receive_exact(self, n):
        """Receive exactly n bytes from socket
        
        Args:
            n: Number of bytes to receive
            
        Returns:
            bytes: Received data, or None if connection closed
        """
        data = b''
        while len(data) < n:
            try:
                chunk = self.socket.recv(n - len(data))
                if not chunk:
                    return None  # Connection closed
                data += chunk
            except socket.timeout:
                if not self.running:
                    return None
                continue
            except socket.error:
                return None
        return data
    
    def send(self, data):
        """Send binary data to the server
        
        Args:
            data: Binary data to send
            
        Returns:
            bool: Success status
        """
        if not self.connected or not self.socket:
            logging.error("Cannot send data: Not connected to server")
            return False
            
        try:
            # Send data length as 4-byte integer first
            data_length = len(data).to_bytes(4, byteorder='big')
            self.socket.sendall(data_length)
            
            # Send actual data
            self.socket.sendall(data)
            logging.debug(f"Sent {len(data)} bytes")
            return True
        except socket.error as e:
            logging.error(f"Failed to send data: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        if not self.connected:
            return
            
        logging.info("Disconnecting from server...")
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            finally:
                self.socket.close()
                self.socket = None
                
        # Wait for receive thread to end
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(2)
            
        logging.info("Disconnected from server")
    
    def is_connected(self):
        """Check if client is connected to the server
        
        Returns:
            bool: Connection status
        """
        return self.connected

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    if client:
        client.disconnect()
    sys.exit(0)

# Create a singleton client instance
client = None

def get_client(server_host='192.168.141.10', server_port=5555, client_ip='192.168.232.10'):
    """Get or create the client instance"""
    global client
    if client is None:
        client = TCPClient(server_host, server_port, client_ip)
    return client

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    client = get_client()
    
    # Simple test - connect and stay connected
    if client.connect():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            client.disconnect()