import asyncio
import sys
import os
import logging

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GodModeTest")

from src.agents.news_agent import NewsSentimentAgent
from src.agents.funding_rate_agent import FundingRateAgent
from src.agents.liquidation_monitor_agent import LiquidationMonitorAgent
from src.data.delta_client import delta_client

async def test_god_mode_agents():
    logger.info("🧪 Testing God Mode Agents...")
    
    symbol = "BTCUSD" # Use a major pair
    
    # 1. Test Data Fetching
    logger.info(f"📡 Fetching Ticker Data for {symbol}...")
    ticker_data = delta_client.get_ticker(symbol)
    logger.info(f"   Ticker Data: {ticker_data.keys() if ticker_data else 'None'}")
    
    if not ticker_data:
        logger.error("❌ Failed to fetch ticker data. Skipping agent tests that depend on it.")
    
    # 2. Test Funding Rate Agent
    logger.info("🤖 Testing FundingRateAgent...")
    funding_agent = FundingRateAgent()
    signal = await funding_agent.analyze(symbol, ticker_data)
    logger.info(f"   Signal: {signal}")
    
    # 3. Test Liquidation Monitor Agent
    logger.info("🤖 Testing LiquidationMonitorAgent...")
    liq_agent = LiquidationMonitorAgent()
    signal = await liq_agent.analyze(symbol, ticker_data)
    logger.info(f"   Signal: {signal}")
    
    # 4. Test News Agent (Requires Internet)
    logger.info("🤖 Testing NewsSentimentAgent (may take a few seconds)...")
    news_agent = NewsSentimentAgent()
    signal = await news_agent.analyze(symbol, None)
    logger.info(f"   Signal: {signal}")

if __name__ == "__main__":
    asyncio.run(test_god_mode_agents())
