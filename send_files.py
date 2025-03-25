#!/usr/bin/env python

import os
import asyncio
import logging
import argparse
from websocket_client import WebSocketClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class FileTransferClient:
    def __init__(self, cdir_path="cdir", ws_client=None, server_uri="ws://192.168.141.10:8765"):
        """Initialize the file transfer client."""
        self.cdir_path = cdir_path
        self.ws_client = ws_client or WebSocketClient(uri=server_uri)
        self.connected_by_self = ws_client is None
        
        # Ensure cdir exists
        if not os.path.exists(self.cdir_path):
            os.makedirs(self.cdir_path)
            logger.info(f"Created directory: {self.cdir_path}")
    
    async def send_files(self):
        """Send all files from cdir to the server using an existing connection."""
        if not os.path.isdir(self.cdir_path):
            logger.error(f"Directory not found: {self.cdir_path}")
            return False
        
        # Check if WebSocket is connected
        if not self.ws_client.running or not self.ws_client.websocket:
            logger.error("No active connection")
            return False
        
        try:
            # Get list of files in cdir
            files = [f for f in os.listdir(self.cdir_path) if os.path.isfile(os.path.join(self.cdir_path, f))]
            
            if not files:
                logger.info(f"No files found in {self.cdir_path}")
                await self.ws_client.send_message("No files to transfer")
                return True
            
            logger.info(f"Found {len(files)} file(s) to transfer")
            
            # Send each file
            for filename in files:
                file_path = os.path.join(self.cdir_path, filename)
                await self.send_file(file_path)
            
            logger.info("All files sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during file transfer: {e}")
            return False
    
    async def send_file(self, file_path):
        """Send a single file to the server."""
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Create file transfer header
            filename = os.path.basename(file_path)
            
            # Format: FILE_BINARY:<filename>:<data>
            # Send filename as header followed by binary content
            header = f"FILE_BINARY:{filename}"
            
            # Send file header
            logger.info(f"Sending file: {filename} ({len(file_content)} bytes)")
            await self.ws_client.send_message(header)
            
            # Send binary content
            await self.ws_client.send_binary(file_content)
            
            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send file {file_path}: {e}")
            return False

    async def run(self):
        """Run the file transfer client with connection handling."""
        if self.connected_by_self:
            # Only connect if we created the WebSocket client
            connected = await self.ws_client.connect()
            if not connected:
                logger.error("Failed to connect to WebSocket server")
                return False
        
        # Send files using the existing connection
        result = await self.send_files()
        
        # Note: We don't disconnect here, as the connection should stay open
        
        return result

async def main():
    """Main function to run the file transfer."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Send files from cdir to server\'s rdir')
    parser.add_argument('--cdir', default='cdir', help='Client directory containing files to send')
    parser.add_argument('--server', default='ws://192.168.141.10:8765', help='WebSocket server URI')
    parser.add_argument('--keep-running', action='store_true', help='Keep the connection running after file transfer')
    args = parser.parse_args()
    
    # Check for existing connection
    from websocket_client import get_active_connection
    ws_client = get_active_connection()
    
    if not ws_client:
        # No active connection, create a new one if possible
        logger.info("No active connection found, creating new connection")
        ws_client = WebSocketClient(uri=args.server)
        connected = await ws_client.connect()
        if not connected:
            logger.error("Failed to connect to WebSocket server")
            return
    else:
        logger.info("Using existing WebSocket connection")
    
    try:
        # Create file transfer client that uses the existing WebSocket connection
        file_client = FileTransferClient(cdir_path=args.cdir, ws_client=ws_client)
        
        # Send files using the existing connection
        await file_client.send_files()
        
        # Keep the connection open if requested
        if args.keep_running:
            logger.info("Keeping connection open. Press Ctrl+C to exit.")
            while True:
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("File transfer interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if not args.keep_running and ws_client and ws_client.connected_by_main:
            # Only disconnect if we created the connection
            await ws_client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("File transfer interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
