#!/usr/bin/env python

import asyncio
import logging
import sys
from websocket_server import WebSocketServer
import file_handler  # This will load and patch the WebSocketServer class

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def main():
    # Create and start the WebSocket server with file handling capability
    server = WebSocketServer(host="192.168.141.10", port=8765)
    logger.info("WebSocket server with file handling capability starting...")
    await server.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutting down")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
