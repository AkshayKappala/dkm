import sys
import os
import logging
import random
import time
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_run")

def send_binary_data(data=None, description="Test binary data"):
    """
    Send binary data over an existing TCP connection
    
    Args:
        data: Binary data to send (generates random data if None)
        description: Description of the data being sent
    
    Returns:
        bool: Whether the message was sent successfully
    """
    # Import tcp_client module to get the established connection
    try:
        # Try to import the module to access the singleton client instance
        from tcp_client import client
        
        # Check if we have an active client connection
        if client is None or not client.is_connected():
            logger.error("No active TCP connection available")
            return False
            
        # If no data provided, generate some random binary data (1024 bytes)
        if data is None:
            data = bytearray(random.getrandbits(8) for _ in range(1024))
            
        # Include a timestamp in the log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] Sending {len(data)} bytes of {description}")
        
        # Send the binary data using the existing connection
        success = client.send_message(data)
        
        if success:
            logger.info(f"Successfully sent {len(data)} bytes")
        else:
            logger.error("Failed to send data")
            
        return success
        
    except ImportError:
        logger.error("TCP client module not found or not properly initialized")
        return False
    except AttributeError as e:
        logger.error(f"TCP client interface error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending data: {e}")
        return False

def main():
    """Parse command line arguments and send binary data"""
    parser = argparse.ArgumentParser(description="Send binary data over existing TCP connection")
    
    parser.add_argument("--file", type=str, help="File to send as binary data")
    parser.add_argument("--text", type=str, help="Text string to send as binary data")
    parser.add_argument("--size", type=int, default=1024, 
                        help="Size of random data to send if no file/text specified")
    
    args = parser.parse_args()
    
    # Determine what data to send
    if args.file:
        try:
            if os.path.exists(args.file):
                with open(args.file, 'rb') as f:
                    file_data = f.read()
                send_binary_data(file_data, f"file data from {args.file}")
            else:
                logger.error(f"File not found: {args.file}")
                return 1
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return 1
            
    elif args.text:
        # Convert text to binary
        text_data = args.text.encode('utf-8')
        send_binary_data(text_data, "text data")
        
    else:
        # Generate random data of specified size
        random_data = bytearray(random.getrandbits(8) for _ in range(args.size))
        send_binary_data(random_data, f"random data ({args.size} bytes)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())