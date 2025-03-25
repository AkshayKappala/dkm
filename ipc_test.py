#!/usr/bin/env python
import sys
import os
import logging
import argparse
import random
from datetime import datetime
from ipc_client import get_ipc_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ipc_test")

def send_through_ipc(data=None, description="Test IPC data", socket_path="/tmp/dkm_ipc.sock"):
    """
    Send binary data through the IPC server
    
    Args:
        data: Binary data to send (generates random data if None)
        description: Description of the data being sent
        socket_path: Path to the IPC socket
    
    Returns:
        bool: Whether the message was sent successfully
    """
    try:
        # Get an IPC client instance
        client = get_ipc_client(socket_path)
        
        # Connect to the IPC server
        if not client.connect():
            logger.error("Failed to connect to IPC server")
            return False
        
        # Check if the TCP connection is up
        if not client.get_connection_status():
            logger.warning("TCP connection is not established")
            if not client.ensure_tcp_connection():
                logger.error("Failed to establish TCP connection")
                return False
            logger.info("TCP connection established")
        
        # If no data provided, generate some random binary data (1024 bytes)
        if data is None:
            data = bytearray(random.getrandbits(8) for _ in range(1024))
        
        # Include a timestamp in the log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] Sending {len(data)} bytes of {description} through IPC")
        
        # Send the binary data using the IPC client
        result = client.send_binary_data(data)
        
        if result:
            logger.info(f"Successfully sent {len(data)} bytes through IPC")
            return True
        else:
            logger.error("Failed to send data through IPC")
            return False
            
    except Exception as e:
        logger.error(f"Error sending data through IPC: {e}")
        return False

def main():
    """Parse command line arguments and send binary data through IPC"""
    parser = argparse.ArgumentParser(description="Send binary data through IPC")
    
    parser.add_argument("--file", type=str, help="File to send as binary data")
    parser.add_argument("--text", type=str, help="Text string to send as binary data")
    parser.add_argument("--size", type=int, default=1024, 
                        help="Size of random data to send if no file/text specified")
    parser.add_argument("--socket", type=str, default="/tmp/dkm_ipc.sock",
                        help="Path to the IPC socket")
    
    args = parser.parse_args()
    
    # Determine what data to send
    if args.file:
        try:
            if os.path.exists(args.file):
                with open(args.file, 'rb') as f:
                    file_data = f.read()
                send_through_ipc(file_data, f"file data from {args.file}", args.socket)
            else:
                logger.error(f"File not found: {args.file}")
                return 1
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return 1
            
    elif args.text:
        # Convert text to binary
        text_data = args.text.encode('utf-8')
        send_through_ipc(text_data, "text data", args.socket)
        
    else:
        # Generate random data of specified size
        random_data = bytearray(random.getrandbits(8) for _ in range(args.size))
        send_through_ipc(random_data, f"random data ({args.size} bytes)", args.socket)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())