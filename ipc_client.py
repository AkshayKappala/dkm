#!/usr/bin/env python
import os
import socket
import json
import struct
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ipc_client")

class IPCClient:
    def __init__(self, socket_path="/tmp/dkm_ipc.sock"):
        """
        Client for interprocess communication with the IPC server
        
        Args:
            socket_path: Path to the Unix domain socket
        """
        self.socket_path = socket_path
        self.sock = None
        self.connected = False
        
    def connect(self, timeout=5):
        """
        Connect to the IPC server
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            bool: Success status
        """
        if self.connected:
            return True
            
        try:
            # Check if socket file exists
            start_time = time.time()
            while not os.path.exists(self.socket_path):
                if time.time() - start_time > timeout:
                    logger.error(f"Socket file not found: {self.socket_path}")
                    return False
                time.sleep(0.1)
                
            # Create socket
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            
            # Connect to the socket
            self.sock.connect(self.socket_path)
            self.connected = True
            
            # Ensure the TCP connection is ready
            if self.ensure_tcp_connection():
                logger.info("Connected to IPC server and TCP connection is ready")
            else:
                logger.warning("Connected to IPC server but TCP connection is not ready")
                
            return True
            
        except socket.error as e:
            logger.error(f"Failed to connect to IPC server: {e}")
            if self.sock:
                self.sock.close()
                self.sock = None
            self.connected = False
            return False
    
    def ensure_tcp_connection(self):
        """
        Ensure that the IPC server has an active TCP connection
        
        Returns:
            bool: Whether the TCP connection is ready
        """
        # Send request to establish TCP connection if needed
        request = {"type": "connect"}
        response = self._send_and_receive(json.dumps(request).encode())
        
        if response and response.get("status") == "ok" and response.get("connected"):
            return True
        return False
    
    def get_connection_status(self):
        """
        Get the status of the TCP connection
        
        Returns:
            bool: Whether the TCP connection is active
        """
        request = {"type": "status"}
        response = self._send_and_receive(json.dumps(request).encode())
        
        if response and response.get("status") == "ok":
            return response.get("connected", False)
        return False
    
    def send_binary_data(self, data, wait_for_response=False):
        """
        Send binary data through the IPC server to the TCP connection
        
        Args:
            data: Binary data to send
            wait_for_response: Whether to wait for a specific response or just ACK
            
        Returns:
            dict or None: Response from server if wait_for_response is True, else None
        """
        if not self.connected:
            if not self.connect():
                return None
        
        response = self._send_and_receive(data)
        
        if wait_for_response:
            return response
        else:
            # Just check if we got an ACK
            return response.get("status") == "ok" if response else False
    
    def _send_and_receive(self, data):
        """
        Send data to the IPC server and receive a response
        
        Args:
            data: Data to send
            
        Returns:
            dict: Parsed response from server, or None on error
        """
        if not self.connected or not self.sock:
            logger.error("Not connected to IPC server")
            return None
            
        try:
            # Send header with message length
            header = struct.pack("!Q", len(data))
            self.sock.sendall(header + data)
            
            # Receive response header (8 bytes for message length)
            header = self._receive_exact(8)
            if not header:
                logger.error("Connection closed while receiving header")
                self.disconnect()
                return None
                
            # Parse header to get response length
            resp_len = struct.unpack("!Q", header)[0]
            
            # Receive the response data
            resp_data = self._receive_exact(resp_len)
            if not resp_data:
                logger.error("Connection closed while receiving data")
                self.disconnect()
                return None
                
            # Try to parse as JSON
            try:
                return json.loads(resp_data)
            except json.JSONDecodeError:
                logger.error("Received non-JSON response")
                return {"status": "error", "message": "Invalid response format"}
                
        except socket.error as e:
            logger.error(f"Socket error: {e}")
            self.disconnect()
            return None
        except Exception as e:
            logger.error(f"Error sending/receiving data: {e}")
            return None
    
    def _receive_exact(self, n):
        """
        Receive exactly n bytes from socket
        
        Args:
            n: Number of bytes to receive
            
        Returns:
            bytes: Received data, or None if connection closed
        """
        data = b''
        while len(data) < n:
            try:
                chunk = self.sock.recv(n - len(data))
                if not chunk:
                    return None  # Connection closed
                data += chunk
            except socket.timeout:
                logger.error("Socket timeout while receiving data")
                return None
            except socket.error:
                return None
        return data
    
    def disconnect(self):
        """Disconnect from the IPC server"""
        if not self.connected:
            return
            
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
            
        self.connected = False
        logger.info("Disconnected from IPC server")

# Create a singleton client instance
_ipc_client = None

def get_ipc_client(socket_path="/tmp/dkm_ipc.sock"):
    """Get or create the IPC client instance"""
    global _ipc_client
    if _ipc_client is None:
        _ipc_client = IPCClient(socket_path)
    return _ipc_client