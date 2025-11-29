import asyncio
import logging
import pandas as pd
from datetime import datetime, timezone, timedelta
from src.data.delta_client import delta_client
from src.data.db_manager import db_manager
from src.data.websocket_client import ws_client

logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self):
        self.running = False

    async def fetch_full_history(self, symbol: str, resolution: str = "1m", start_year: int = 2020):
        """
        🚀 GOD MODE: Fetches ALL historical data from start_year to NOW.
        Handles pagination automatically.
        """
        logger.info(f"⏳ STARTING DEEP HISTORY FETCH FOR {symbol}...")
        
        # Calculate start timestamp
        start_date = datetime(start_year, 1, 1, tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)
        
        # We fetch continuously until we reach current time
        fetch_start = int(start_date.timestamp())
        fetch_end = int(current_time.timestamp())
        
        total_candles = 0
        
        while fetch_start < fetch_end:
            # Request next batch (Delta limit is usually ~2000 per call)
            # We request a bit more time range, but limit handles the count
            next_batch_end = fetch_start + (2000 * 60) # Approx 2000 minutes ahead
            
            # API Call
            try:
                # Delta API uses 'start' and 'end' in epoch seconds
                response = delta_client.get_history(
                    symbol, 
                    resolution, 
                    start=fetch_start, 
                    end=next_batch_end
                )
            except Exception as e:
                logger.error(f"❌ API Fail: {e}")
                await asyncio.sleep(5)
                continue

            if 'result' not in response or not response['result']:
                logger.warning(f"⚠️ No data found for range {fetch_start} to {next_batch_end}")
                # Jump forward to avoid infinite loop
                fetch_start = next_batch_end
                continue

            candles = response['result']
            
            # Process & Clean
            processed_candles = []
            last_timestamp = fetch_start
            
            for c in candles:
                ts_val = c['time']
                processed_candles.append({
                    'timestamp': datetime.fromtimestamp(ts_val, tz=timezone.utc),
                    'open': float(c['open']),
                    'high': float(c['high']),
                    'low': float(c['low']),
                    'close': float(c['close']),
                    'volume': float(c['volume'])
                })
                # Update last timestamp found
                if ts_val > last_timestamp:
                    last_timestamp = ts_val

            # Store in DB
            if processed_candles:
                await db_manager.store_ohlc(symbol, processed_candles)
                total_candles += len(processed_candles)
                logger.info(f"✅ Stored batch: {len(processed_candles)} candles. (Last: {processed_candles[-1]['timestamp']})")
            
            # 🔄 PAGINATION LOGIC:
            # Set next start time to the last candle we received + 1 second
            fetch_start = last_timestamp + 1
            
            # Respect Rate Limits
            await asyncio.sleep(0.5)

        logger.info(f"🎉 HISTORY FETCH COMPLETE! Total Candles: {total_candles}")

data_pipeline = DataPipeline()
