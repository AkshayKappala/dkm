#!/usr/bin/env python

import os
import json
import base64
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
    def __init__(self, cdir_path="cdir", server_uri="ws://192.168.141.10:8765"):
        """Initialize the file transfer client."""
        self.cdir_path = cdir_path
        self.ws_client = WebSocketClient(uri=server_uri)
        
        # Ensure cdir exists
        if not os.path.exists(self.cdir_path):
            os.makedirs(self.cdir_path)
            logger.info(f"Created directory: {self.cdir_path}")
    
    async def send_files(self):
        """Send all files from cdir to the server."""
        if not os.path.isdir(self.cdir_path):
            logger.error(f"Directory not found: {self.cdir_path}")
            return False
        
        # Connect to the WebSocket server
        connected = await self.ws_client.connect()
        if not connected:
            logger.error("Failed to connect to WebSocket server")
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
        finally:
            # Always disconnect when done
            await self.ws_client.disconnect()
    
    async def send_file(self, file_path):
        """Send a single file to the server."""
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Encode file content as base64
            content_b64 = base64.b64encode(file_content).decode('utf-8')
            
            # Create file transfer payload
            filename = os.path.basename(file_path)
            file_data = {
                "filename": filename,
                "content": content_b64
            }
            
            # Create file transfer message
            message = f"FILE_TRANSFER:{json.dumps(file_data)}"
            
            # Send file
            logger.info(f"Sending file: {filename} ({len(file_content)} bytes)")
            await self.ws_client.send_message(message)
            
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
    parser.add_argument('--server', default='ws://192.168.141.10:8765', help='WebSocket server URI')
    args = parser.parse_args()
    
    # Create and run file transfer client
    file_client = FileTransferClient(cdir_path=args.cdir, server_uri=args.server)
    await file_client.send_files()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("File transfer interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
