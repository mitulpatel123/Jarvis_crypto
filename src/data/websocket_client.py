import asyncio
import websockets
import json
import logging
from typing import List, Callable, Dict

logger = logging.getLogger(__name__)

class WebSocketClient:
    URL = "wss://socket.india.delta.exchange"

    def __init__(self):
        self.connection = None
        self.callbacks: Dict[str, List[Callable]] = {}
        self.running = False

    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.connection = await websockets.connect(self.URL)
            self.running = True
            logger.info("Connected to WebSocket.")
            asyncio.create_task(self._listen())
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.running = False

    async def subscribe(self, channel: str, symbols: List[str]):
        """
        Subscribe to a channel for specific symbols.
        channel: e.g., 'v2/ticker'
        """
        if not self.connection:
            logger.warning("Cannot subscribe: No connection.")
            return

        payload = {
            "type": "subscribe",
            "payload": {
                "channels": [
                    {
                        "name": channel,
                        "symbols": symbols
                    }
                ]
            }
        }
        await self.connection.send(json.dumps(payload))
        logger.info(f"Subscribed to {channel} for {symbols}")

    def on_message(self, channel: str, callback: Callable):
        """Register a callback for a specific channel."""
        if channel not in self.callbacks:
            self.callbacks[channel] = []
        self.callbacks[channel].append(callback)

    async def _listen(self):
        """Listen for incoming messages."""
        while self.running and self.connection:
            try:
                message = await self.connection.recv()
                data = json.loads(message)
                
                # Dispatch to callbacks
                # Delta messages usually have a 'type' or 'channel' field?
                # Need to verify message structure. Usually it's like:
                # {"type": "v2/ticker", "symbol": "BTCUSD", ...}
                # or {"channel": "v2/ticker", ...}
                
                # For now, let's assume we can dispatch based on 'type' or just log
                msg_type = data.get('type')
                if msg_type and msg_type in self.callbacks:
                    for cb in self.callbacks[msg_type]:
                        await cb(data)
                
                # Also check if it's a subscription confirmation
                if data.get('type') == 'subscriptions':
                    logger.info(f"Subscription confirmed: {data}")

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed.")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error reading message: {e}")

    async def disconnect(self):
        """Close the connection."""
        self.running = False
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from WebSocket.")

ws_client = WebSocketClient()
