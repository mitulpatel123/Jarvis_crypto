import asyncio
import logging
import sys
import pandas as pd
from src.data.groq_client import groq_client
from src.agents.news_agent import NewsSentimentAgent
from src.agents.main_brain import MainBrain
from src.agents.pattern_agent import PatternRecognitionAgent
from src.agents.momentum_agent import MomentumAgent
from src.agents.base_agent import Signal

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

async def main():
    symbol = "BTCUSD"
    print(f"--- Verifying Phase 3 for {symbol} ---")

    # 1. Test Groq Connection (Simple)
    print("\n[1] Testing Groq Connection...")
    try:
        msg = groq_client.query(
            messages=[{"role": "user", "content": "Say 'Hello Jarvis'"}],
            model="openai/gpt-oss-120b"
        )
        print(f"✅ Groq Response: {msg.content}")
    except Exception as e:
        print(f"❌ Groq Failed: {e}")
        # Continue to test other parts if possible, but MainBrain will fail

    # 2. Test News Agent (Browser Automation)
    print("\n[2] Testing NewsSentimentAgent (Browser Automation)...")
    news_agent = NewsSentimentAgent()
    try:
        news_signal = await news_agent.analyze(symbol)
        print(f"✅ News Signal: {news_signal}")
    except Exception as e:
        print(f"❌ News Agent Failed: {e}")
        news_signal = Signal(agent_name="NewsSentimentAgent", symbol=symbol, action="NEUTRAL", confidence=0.0)

    # 3. Test Advanced Agents (Real Data)
    print("\n[3] Testing Advanced Agents (Real Data)...")
    from src.data.delta_client import delta_client
    
    try:
        # Fetch real history
        history = delta_client.get_history(symbol, resolution="1d", limit=30)
        if 'result' not in history:
            print("❌ Failed to fetch real history")
            return

        candles = history['result']
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        # Ensure numeric columns
        cols = ['open', 'high', 'low', 'close', 'volume']
        for c in cols:
            df[c] = pd.to_numeric(df[c])
            
        print(f"✅ Fetched {len(df)} real candles for {symbol}")
        
        pattern_agent = PatternRecognitionAgent()
        momentum_agent = MomentumAgent()
        
        p_sig = await pattern_agent.analyze(symbol, df)
        m_sig = await momentum_agent.analyze(symbol, df)
        print(f"✅ Pattern Signal: {p_sig}")
        print(f"✅ Momentum Signal: {m_sig}")
        
    except Exception as e:
        print(f"❌ Real Data Test Failed: {e}")
        return

    # 4. Test Main Brain (Aggregation)
    print("\n[4] Testing Main Brain...")
    main_brain = MainBrain()
    
    # Simulate signals from all agents
    mock_signals = [
        news_signal,
        p_sig,
        m_sig,
        Signal(agent_name="TrendAgent", symbol=symbol, action="BUY", confidence=0.8, metadata={}),
        Signal(agent_name="VolumeAgent", symbol=symbol, action="BUY", confidence=0.7, metadata={})
    ]
    
    try:
        final_decision = await main_brain.analyze(symbol, mock_signals)
        print(f"✅ Final Decision: {final_decision}")
    except Exception as e:
        print(f"❌ Main Brain Failed: {e}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
