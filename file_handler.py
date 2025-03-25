#!/usr/bin/env python

import os
import logging
from websocket_server import WebSocketServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class FileHandlerServer:
    def __init__(self, rdir_path="rdir"):
        """Initialize the file handler with the destination directory."""
        self.rdir_path = rdir_path
        self.current_file = None
        
        # Create the destination directory if it doesn't exist
        os.makedirs(self.rdir_path, exist_ok=True)
        logger.info(f"File handler initialized. Files will be saved to: {self.rdir_path}")
        
        # Patch the WebSocketServer class to intercept messages
        self._patch_websocket_server()
    
    def _patch_websocket_server(self):
        """Patch the WebSocketServer class to intercept and process file transfers."""
        original_handle_client = WebSocketServer.handle_client
        
        async def patched_handle_client(self_server, websocket):
            client_name = await self_server.register_client(websocket)
            
            try:
                # Send welcome message
                client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
                await websocket.send(f"Welcome! You are {client_name}")
                
                # Handle incoming messages
                async for message in websocket:
                    # Binary message - file content
                    if isinstance(message, bytes) and self.current_file:
                        await self.handle_binary_data(message, client_name)
                    # Text message
                    elif isinstance(message, str):
                        # Check if it's a file transfer header
                        if message.startswith("FILE_BINARY:"):
                            filename = message[12:]  # Extract filename
                            self.prepare_file_receive(filename, client_name)
                        else:
                            # Regular message, broadcast as usual
                            await self_server.broadcast(f"{client_name}: {message}")
                    
            except Exception as e:
                logger.error(f"Error handling client {client_name}: {e}")
            finally:
                await self_server.unregister_client(websocket)
                self.current_file = None
        
        # Replace the original method with our patched version
        WebSocketServer.handle_client = patched_handle_client
    
    def prepare_file_receive(self, filename, client_name):
        """Prepare to receive a file with the given name."""
        try:
            # Create safe filename (just the basename)
            safe_filename = os.path.basename(filename)
            output_path = os.path.join(self.rdir_path, safe_filename)
            
            # Store current file info
            self.current_file = {
                'filename': safe_filename,
                'path': output_path,
                'client': client_name
            }
            
            logger.info(f"Preparing to receive file: {safe_filename} from {client_name}")
            
        except Exception as e:
            logger.error(f"Error preparing file receive: {e}")
            self.current_file = None
    
    async def handle_binary_data(self, data, client_name):
        """Process incoming binary file data."""
        try:
            if not self.current_file:
                logger.error("Received binary data without file header")
                return
                
            # Write the binary data to the file
            with open(self.current_file['path'], 'wb') as f:
                f.write(data)
            
            logger.info(f"File received from {client_name}: {self.current_file['filename']}, Size: {len(data)} bytes")
            
            # Reset current file
            self.current_file = None
            
        except Exception as e:
            logger.error(f"Error processing file data: {e}")
            self.current_file = None

# Initialize the file handler when imported
file_handler = FileHandlerServer()
logger.info("File handler server started")
