import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.base_agent import Signal
from src.agents.main_brain import MainBrain
from src.agents.whale_movement_agent import WhaleMovementAgent
from src.agents.sentiment_aggregation_agent import SentimentAggregationAgent

async def test_signal_instantiation():
    print("🧪 Testing Signal Instantiation...")
    
    # Test 1: Direct Signal Creation
    try:
        s = Signal(agent_name="Test", symbol="BTC/USD", action="BUY", confidence=0.9, metadata={})
        print("✅ Direct Signal creation passed.")
    except Exception as e:
        print(f"❌ Direct Signal creation failed: {e}")
        return

    # Test 2: MainBrain Error Handling (which creates a Signal)
    brain = MainBrain()
    try:
        # Trigger an error by passing invalid data to analyze
        # This should trigger the exception handler which returns a Signal
        # We need to mock logger to avoid clutter or just ignore it
        res = await brain.analyze("BTC/USD", data="INVALID_DATA")
        print(f"✅ MainBrain error handling passed. Result: {res}")
    except Exception as e:
        print(f"❌ MainBrain error handling failed: {e}")

    # Test 3: WhaleMovementAgent
    whale = WhaleMovementAgent()
    try:
        # Test empty data (neutral signal)
        res = await whale.analyze("BTC/USD", None)
        print(f"✅ WhaleMovementAgent (Empty) passed. Result: {res}")
    except Exception as e:
        print(f"❌ WhaleMovementAgent (Empty) failed: {e}")

    # Test 4: SentimentAggregationAgent
    sentiment = SentimentAggregationAgent()
    try:
        res = await sentiment.analyze("BTC/USD", None)
        print(f"✅ SentimentAggregationAgent passed. Result: {res}")
    except Exception as e:
        print(f"❌ SentimentAggregationAgent failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_signal_instantiation())
