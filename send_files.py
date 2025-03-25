#!/usr/bin/env python

import os
import asyncio
import logging
import argparse
from websocket_client import WebSocketClient, get_active_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class FileTransferClient:
    def __init__(self, cdir_path="cdir", ws_client=None):
        """Initialize the file transfer client."""
        self.cdir_path = cdir_path
        self.ws_client = ws_client
        
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
        if not self.ws_client or not self.ws_client.running or not self.ws_client.websocket:
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
            
            # Format: FILE_BINARY:<filename>
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

async def main():
    """Main function to run the file transfer."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Send files from cdir to server\'s rdir')
    parser.add_argument('--cdir', default='cdir', help='Client directory containing files to send')
    args = parser.parse_args()
    
    # Check for existing connection
    ws_client = get_active_connection()
    
    if not ws_client:
        # No active connection found
        logger.error("No active connection found. Please run websocket_client.py first.")
        return
    
    try:
        # Create file transfer client that uses the existing WebSocket connection
        file_client = FileTransferClient(cdir_path=args.cdir, ws_client=ws_client)
        
        # Send files using the existing connection
        await file_client.send_files()
                
    except KeyboardInterrupt:
        logger.info("File transfer interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("File transfer interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
