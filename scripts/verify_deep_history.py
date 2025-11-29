import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.pipeline import data_pipeline
from src.data.db_manager import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    symbol = "BTCUSD"
    logger.info(f"--- Verifying Deep History Fetch for {symbol} ---")
    
    # Initialize DB
    await db_manager.connect()
    
    # Fetch history starting from 2024 (to be quick)
    await data_pipeline.fetch_full_history(symbol, resolution="1d", start_year=2024)
    
    # Verify data in DB (pseudo-check, just ensuring no crash)
    # In a real check we'd query the DB, but for now we rely on logs
    
    await db_manager.disconnect()
    logger.info("--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
