import asyncio
import pandas as pd
from src.data.delta_client import delta_client
from src.agents.technical_agent import TechnicalAnalysisAgent
from src.agents.trend_agent import TrendFollowingAgent
from src.agents.volatility_agent import VolatilityAgent
from src.agents.volume_agent import VolumeAnalysisAgent
import logging
import sys

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


async def main():
    symbol = "BTCUSD"
    print(f"--- Verifying Foundation for {symbol} ---")

    # 1. Test Delta API Connection
    print("\n[1] Testing Delta API Connection...")
    try:
        ticker_response = delta_client.get_ticker(symbol)
        tickers = ticker_response['result']
        
        # Filter for specific symbol
        target_ticker = next((t for t in tickers if t['symbol'] == symbol), None)
        
        if target_ticker:
            print(f"✅ Ticker Fetch Success: {symbol}")
            print(f"   Close: {target_ticker.get('close')}")
            print(f"   Mark: {target_ticker.get('mark_price')}")
        else:
            print(f"❌ Ticker {symbol} not found in response!")
            # Print first 5 tickers to see what's there
            print("First 5 tickers found:")
            for t in tickers[:5]:
                print(f"   {t['symbol']}")
            return
            
    except Exception as e:
        print(f"❌ Ticker Fetch Failed: {e}")
        return

    # 2. Fetch Historical Data
    print("\n[2] Fetching Historical Data...")
    try:
        # Try different resolution and limit
        history = delta_client.get_history(symbol, resolution="1d", limit=10)
        if 'result' not in history:
             print(f"❌ History response missing 'result': {history}")
             return
             
        candles = history['result']
        df = pd.DataFrame(candles)
        # Ensure correct types
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['open'] = df['open'].astype(float)
        df['volume'] = df['volume'].astype(float)
        # Sort by time just in case
        df = df.sort_values('time')
        print(f"✅ Data Fetch Success: {len(df)} candles")
    except Exception as e:
        print(f"❌ Data Fetch Failed: {e}")
        return

    # 3. Test Agents
    print("\n[3] Testing Agents...")
    agents = [
        TechnicalAnalysisAgent(),
        TrendFollowingAgent(),
        VolatilityAgent(),
        VolumeAnalysisAgent()
    ]

    for agent in agents:
        try:
            signal = await agent.analyze(symbol, df)
            print(f"✅ {agent.name}: Action={signal.action}, Conf={signal.confidence:.2f}")
            print(f"   Metadata: {signal.metadata}")
        except Exception as e:
            print(f"❌ {agent.name} Failed: {e}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
