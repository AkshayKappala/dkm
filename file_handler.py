#!/usr/bin/env python

import os
import json
import base64
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
                await websocket.send(f"Welcome! You are {client_name} connecting from IP {client_ip}")
                
                # Handle incoming messages
                async for message in websocket:
                    logger.debug(f"Message from {client_name} ({client_ip}): {message}")
                    
                    # Check if it's a file transfer message
                    if message.startswith("FILE_TRANSFER:"):
                        await self.handle_file_transfer(message[13:], client_name, client_ip)
                    else:
                        # Regular message, broadcast as usual
                        await self_server.broadcast(f"{client_name} ({client_ip}): {message}")
                    
            except Exception as e:
                logger.error(f"Error handling client {client_name}: {e}")
            finally:
                await self_server.unregister_client(websocket)
        
        # Replace the original method with our patched version
        WebSocketServer.handle_client = patched_handle_client
    
    async def handle_file_transfer(self, file_data, client_name, client_ip):
        """Process incoming file transfer data."""
        try:
            # Parse the file transfer data
            file_info = json.loads(file_data)
            filename = file_info.get("filename")
            content_b64 = file_info.get("content")
            
            if not filename or not content_b64:
                logger.error("Invalid file transfer data: missing filename or content")
                return
            
            # Decode the base64 content
            file_content = base64.b64decode(content_b64)
            
            # Create full path ensuring it's within rdir
            safe_filename = os.path.basename(filename)
            output_path = os.path.join(self.rdir_path, safe_filename)
            
            # Save the file
            with open(output_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"File received from {client_name} ({client_ip}): {safe_filename}, Size: {len(file_content)} bytes")
            
        except json.JSONDecodeError:
            logger.error("Failed to parse file transfer data as JSON")
        except Exception as e:
            logger.error(f"Error processing file transfer: {e}")

# Initialize the file handler when imported
file_handler = FileHandlerServer()
logger.info("File handler server started")
