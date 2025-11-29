import asyncio
import logging
from datetime import datetime, timezone
from src.data.delta_client import delta_client
from src.data.db_manager import db_manager

logger = logging.getLogger(__name__)

from src.data.websocket_client import ws_client

class DataPipeline:
    def __init__(self):
        self.running = False

    async def fetch_and_store_ohlc(self, symbol: str, resolution: str = "1m", limit: int = 100):
        """
        Fetch OHLC data from Delta and store it in the database.
        """
        try:
            logger.info(f"Fetching {resolution} candles for {symbol}...")
            response = delta_client.get_history(symbol, resolution, limit=limit)
            
            if 'result' not in response:
                logger.error(f"Invalid response for {symbol}: {response}")
                return

            candles = response['result']
            if not candles:
                logger.warning(f"No candles returned for {symbol}")
                return

            # Process candles
            processed_candles = []
            for c in candles:
                # Convert timestamp (seconds) to datetime
                ts = datetime.fromtimestamp(c['time'], tz=timezone.utc)
                processed_candles.append({
                    'timestamp': ts,
                    'open': float(c['open']),
                    'high': float(c['high']),
                    'low': float(c['low']),
                    'close': float(c['close']),
                    'volume': float(c['volume'])
                })

            # Store in DB
            await db_manager.store_ohlc(symbol, processed_candles)
            logger.info(f"Stored {len(processed_candles)} candles for {symbol}")

        except Exception as e:
            logger.error(f"Error in data pipeline for {symbol}: {e}")

    async def start_realtime_stream(self, symbols: list):
        """
        Start real-time data streaming via WebSocket.
        """
        await ws_client.connect()
        
        # Define callback for ticker updates
        async def on_ticker_update(data):
            # Log or process ticker data
            # Example data structure needs verification, but usually contains symbol and price
            logger.info(f"Real-time Update: {data}")
            
        # Register callback
        ws_client.on_message('v2/ticker', on_ticker_update)
        
        # Subscribe to ticker channel
        await ws_client.subscribe('v2/ticker', symbols)
        
        # Keep running
        self.running = True
        while self.running:
            await asyncio.sleep(1)

data_pipeline = DataPipeline()
