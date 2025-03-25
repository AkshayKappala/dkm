#!/usr/bin/env python
# filepath: websocket_client.py

import asyncio
import websockets
import logging
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global variable to track active connection
_active_connection = None

def get_active_connection():
    """Return the active WebSocket client connection if one exists."""
    global _active_connection
    if _active_connection and _active_connection.running:
        return _active_connection
    return None

class WebSocketClient:
    def __init__(self, uri="ws://192.168.141.10:8765"):  # Updated to match the server's IP address
        self.uri = uri
        self.websocket = None
        self.running = False
        self.reconnect_delay = 1  # Start with 1 second delay for reconnection attempts
        self.max_reconnect_delay = 30  # Max 30 seconds between reconnection attempts
        self.connected_by_main = False
        
    async def connect(self):
        """Establish connection to the WebSocket server."""
        global _active_connection
        try:
            self.websocket = await websockets.connect(
                self.uri,
                ping_interval=30,
                ping_timeout=10
            )
            self.running = True
            self.reconnect_delay = 1  # Reset reconnect delay after successful connection
            self.connected_by_main = True
            _active_connection = self
            logger.info(f"Connected to {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
            
    async def send_message(self, message):
        """Send a text message to the server."""
        if not self.websocket or not self.running:
            logger.error("Cannot send message - not connected")
            return False
            
        try:
            await self.websocket.send(message)
            logger.debug(f"Sent message: {message}")
            return True
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed while sending message")
            self.running = False
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def send_binary(self, binary_data):
        """Send binary data to the server."""
        if not self.websocket or not self.running:
            logger.error("Cannot send binary data - not connected")
            return False
            
        try:
            await self.websocket.send(binary_data)
            return True
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed while sending binary data")
            self.running = False
            return False
        except Exception as e:
            logger.error(f"Error sending binary data: {e}")
            return False
    
    async def receive_messages(self):
        """Receive and process messages from the server."""
        if not self.websocket:
            logger.error("Cannot receive messages - not connected")
            return
            
        try:
            while self.running:
                message = await self.websocket.recv()
                if isinstance(message, bytes):
                    logger.info(f"Received binary data: {len(message)} bytes")
                else:
                    logger.info(f"Received: {message}")
                # Here you can add custom message handling logic
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed by server")
            self.running = False
        except asyncio.CancelledError:
            logger.info("Message receiving task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            self.running = False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        global _active_connection
        if self.websocket:
            try:
                self.running = False
                if _active_connection == self:
                    _active_connection = None
                await self.websocket.close()
                logger.info("Disconnected from server")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
            finally:
                self.websocket = None
    
    async def run(self):
        """Main client loop with reconnection logic."""
        while True:
            connected = await self.connect()
            
            if connected:
                # Start receiving messages
                receiver_task = asyncio.create_task(self.receive_messages())
                
                # Keep the connection alive until explicitly closed
                while self.running:
                    await asyncio.sleep(1)
                    
                # Cleanup receiver task
                if not receiver_task.done():
                    receiver_task.cancel()
                    try:
                        await receiver_task
                    except asyncio.CancelledError:
                        pass
                
                await self.disconnect()
                
                # If we're intentionally stopping, break out of the loop
                if not self.running:
                    break
            
            # Wait before attempting to reconnect
            logger.info(f"Attempting to reconnect in {self.reconnect_delay} seconds...")
            await asyncio.sleep(self.reconnect_delay)
            
            # Exponential backoff with a maximum delay
            self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)

async def shutdown(client):
    """Handle graceful shutdown."""
    logger.info("Shutting down...")
    client.running = False
    await client.disconnect()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    asyncio.get_event_loop().stop()

async def main():
    # Setup signal handlers
    loop = asyncio.get_running_loop()
    client = WebSocketClient()
    
    # Handle Ctrl+C gracefully
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(client)))
    
    # Basic client interaction demo
    try:
        # Start the client in the background
        client_task = asyncio.create_task(client.run())
        
        # Wait for initial connection
        await asyncio.sleep(2)
        
        if client.running:
            # Send a test message
            await client.send_message("Hello from client!")
            
            # Keep the program running
            while client.running:
                await asyncio.sleep(1)
                
        await client_task
        
    except asyncio.CancelledError:
        logger.info("Client execution cancelled")
    finally:
        if not client_task.done():
            client_task.cancel()
            try:
                await client_task
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)