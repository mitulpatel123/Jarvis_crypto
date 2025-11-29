import asyncio
import logging
import sys
from src.data.pipeline import data_pipeline

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

async def main():
    symbol = "BTCUSD"
    print(f"--- Verifying Data Pipeline for {symbol} ---")

    # 1. Test OHLC Fetch & Store
    print("\n[1] Testing OHLC Fetch & Store...")
    await data_pipeline.fetch_and_store_ohlc(symbol, resolution="1d", limit=5)
    
    # 2. Test Real-time Stream
    print("\n[2] Testing Real-time Stream (Running for 10 seconds)...")
    try:
        # Start stream in background
        stream_task = asyncio.create_task(data_pipeline.start_realtime_stream([symbol]))
        
        # Wait for 10 seconds to see logs
        await asyncio.sleep(10)
        
        # Stop
        data_pipeline.running = False
        stream_task.cancel()
        print("Stopped stream.")
        
    except Exception as e:
        print(f"❌ Stream Failed: {e}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
