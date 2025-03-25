#!/usr/bin/env python
# filepath: websocket_server.py

import asyncio
import websockets
import logging
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = {}  # {websocket: client_name}
        self.next_client_id = 1
        self.available_ids = deque()  # Recycled client IDs
        self.lock = asyncio.Lock()  # For thread-safe client management
        
    async def register_client(self, websocket):
        """Register a new client with a unique name."""
        async with self.lock:
            if self.available_ids:
                # Reuse available IDs from disconnected clients
                client_id = self.available_ids.popleft()
            else:
                client_id = self.next_client_id
                self.next_client_id += 1
                
            client_name = f"client{client_id}"
            self.clients[websocket] = client_name
            logger.info(f"New client connected: {client_name}")
            
            # Notify everyone about the new client
            await self.broadcast(f"SERVER: {client_name} has joined. {len(self.clients)} clients connected.")
            return client_name

    async def unregister_client(self, websocket):
        """Unregister a client when they disconnect."""
        async with self.lock:
            if websocket in self.clients:
                client_name = self.clients[websocket]
                # Extract client ID number and add back to available IDs
                try:
                    client_id = int(client_name.replace("client", ""))
                    self.available_ids.append(client_id)
                except ValueError:
                    pass  # Skip if client name doesn't follow expected format
                
                # Remove from active clients
                del self.clients[websocket]
                logger.info(f"Client disconnected: {client_name}")
                
                # Notify remaining clients
                await self.broadcast(f"SERVER: {client_name} has left. {len(self.clients)} clients connected.")

    async def broadcast(self, message):
        """Send a message to all connected clients."""
        if not self.clients:  # No clients connected
            return
            
        # Create a list of coroutines to send the message to each client
        coroutines = [
            self.send_to_client(websocket, message) 
            for websocket in self.clients.keys()
        ]
        
        # Execute all send operations concurrently and collect results
        await asyncio.gather(*coroutines, return_exceptions=True)

    async def send_to_client(self, websocket, message):
        """Send a message to a specific client with error handling."""
        try:
            await websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            logger.debug(f"Failed to send message - connection already closed")
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def handle_client(self, websocket):
        """Handle a client connection."""
        client_name = await self.register_client(websocket)
        
        try:
            # Send welcome message to the new client
            await websocket.send(f"Welcome! You are {client_name}")
            
            # Handle incoming messages
            async for message in websocket:
                logger.debug(f"Message from {client_name}: {message}")
                
                # Broadcast the message to all clients with sender's name
                await self.broadcast(f"{client_name}: {message}")
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed for {client_name}")
        except Exception as e:
            logger.error(f"Error handling client {client_name}: {e}")
        finally:
            # Always ensure client is unregistered on disconnect
            await self.unregister_client(websocket)

    async def start_server(self):
        """Start the WebSocket server."""
        try:
            server = await websockets.serve(
                self.handle_client, 
                self.host, 
                self.port,
                ping_interval=30,  # Send ping every 30 seconds
                ping_timeout=10    # Wait 10 seconds for pong response
            )
            
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
            
            # Keep the server running
            await server.wait_closed()
        except Exception as e:
            logger.error(f"Server error: {e}")

if __name__ == "__main__":
    # Set the specific IP address 192.168.232.10
    server = WebSocketServer(host="192.168.232.10", port=8765)
    try:
        # Start the server with proper shutdown handling
        loop = asyncio.get_event_loop()
        loop.run_until_complete(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server shutting down")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")