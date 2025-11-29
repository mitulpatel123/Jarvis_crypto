import asyncio
import logging
import sys
import pandas as pd
import pkgutil
import importlib
import os
import time
from datetime import datetime, timezone, timedelta
from typing import List

# Configure logging
logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JarvisCore")

from src.data.delta_client import delta_client
from src.agents.base_agent import Signal
from src.agents.main_brain import MainBrain
from src.execution.executor import executor
from src.learning.judge import TheJudge
from src.data.db_manager import db_manager
from src.config.settings import settings

class JarvisEngine:
    def __init__(self):
        self.running = False
        self.main_brain = MainBrain()
        self.judge = TheJudge()
        self.agents = self.load_all_agents()
        self.mode = settings.TRADING_MODE.upper() # BACKTEST, PAPER, LIVE

    def load_all_agents(self):
        agents = []
        package_path = "src/agents"
        for _, name, _ in pkgutil.iter_modules([package_path]):
            if name in ["base_agent", "main_brain"]: continue
            try:
                module = importlib.import_module(f"src.agents.{name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and attr_name.endswith("Agent") and attr_name != "BaseAgent":
                        agents.append(attr())
                        logger.info(f"✅ Loaded Agent: {attr_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load {name}: {e}")
        return agents

    async def run_backtest(self, symbol="BTCUSD", days=30):
        """Mode 1: Paper Trade on Historical Data"""
        logger.info(f"📜 STARTING BACKTEST: {symbol} for last {days} days")
        
        # 1. Fetch History
        end_time = int(time.time())
        start_time = end_time - (days * 24 * 60 * 60)
        
        response = delta_client.get_history(symbol, "1h", start=start_time, end=end_time, limit=2000)
        if 'result' not in response:
            logger.error("No historical data found.")
            return

        df = pd.DataFrame(response['result'])
        cols = ['open', 'high', 'low', 'close', 'volume']
        for c in cols: df[c] = pd.to_numeric(df[c])
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.sort_values('time')

        # 2. Simulate Candle by Candle
        for i in range(50, len(df)):
            # Window of data the bot "sees"
            current_window = df.iloc[:i] 
            current_candle = df.iloc[i]
            current_price = float(current_candle['close'])
            timestamp = current_candle['time']

            logger.info(f"⏳ Replaying {timestamp} | Price: {current_price}")

            # Run Agents
            agent_tasks = [agent.analyze(symbol, current_window) for agent in self.agents]
            signals = await asyncio.gather(*agent_tasks)

            # Brain Decision
            decision = await self.main_brain.analyze(symbol, signals)

            # Execute (In Backtest Mode, Executor just logs DB)
            if decision.confidence > 0.75 and decision.action in ["BUY", "SELL"]:
                await executor.execute_order(
                    symbol=symbol,
                    action=decision.action,
                    confidence=decision.confidence,
                    current_price=current_price,
                    atr=current_price * 0.02,
                    mode="BACKTEST",
                    timestamp=timestamp
                )

        logger.info("🏁 Backtest Complete. Check Dashboard for Results.")

    async def run_live_scanner(self):
        """Mode 2 & 3: Paper/Live Trading on Real Data"""
        logger.info(f"📡 STARTING {self.mode} SCANNER...")
        
        while self.running:
            try:
                # 1. Get Active Ocean (Top Volume coins)
                # Note: We filter for 'perpetual_futures' to ensure liquidity
                products = delta_client.get_products().get('result', [])
                opportunities = [p['symbol'] for p in products if p['contract_type'] == 'perpetual_futures'][:10] # Scan Top 10 for speed
                
                logger.info(f"🌊 Scanning Ocean: {len(opportunities)} Assets")

                for symbol in opportunities:
                    # Fetch Live Data
                    history = delta_client.get_history(symbol, "1h", limit=50)
                    if not history or 'result' not in history: continue
                    
                    df = pd.DataFrame(history['result'])
                    cols = ['open', 'high', 'low', 'close', 'volume']
                    for c in cols: df[c] = pd.to_numeric(df[c])
                    
                    current_price = float(df['close'].iloc[-1])

                    # Analyze
                    agent_tasks = [agent.analyze(symbol, df) for agent in self.agents]
                    signals = await asyncio.gather(*agent_tasks)
                    
                    decision = await self.main_brain.analyze(symbol, signals)

                    # Execute
                    if decision.confidence > 0.8 and decision.action in ["BUY", "SELL"]:
                        logger.info(f"🚀 OPPORTUNITY: {symbol} {decision.action}")
                        await executor.execute_order(
                            symbol=symbol,
                            action=decision.action,
                            confidence=decision.confidence,
                            current_price=current_price,
                            atr=current_price * 0.02,
                            mode=self.mode
                        )
                    
                    # Rate Limit Protection
                    await asyncio.sleep(1) 

                # Run The Judge (Self-Improvement)
                await self.judge.review_performance()
                
            except Exception as e:
                logger.error(f"Scanner Loop Error: {e}")
                await asyncio.sleep(5)

    async def start(self):
        self.running = True
        await db_manager.connect()
        
        if self.mode == "BACKTEST":
            await self.run_backtest()
        else:
            await self.run_live_scanner()

if __name__ == "__main__":
    # Auto-launch UI
    import subprocess
    try:
        subprocess.Popen(["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.headless=true"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("📊 Neural Dashboard Launched: http://localhost:8501")
    except Exception as e:
        logger.warning(f"Failed to launch UI: {e}")

    engine = JarvisEngine()
    try:
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
