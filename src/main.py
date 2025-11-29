import asyncio
import logging
import sys
import pandas as pd
import pkgutil
import importlib
import os
from typing import List
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.data.delta_client import delta_client
from src.agents.base_agent import Signal
from src.agents.main_brain import MainBrain
from src.execution.executor import executor
from src.learning.judge import TheJudge
from src.data.db_manager import db_manager

class JarvisScanner:
    def __init__(self):
        self.running = False
        self.main_brain = MainBrain()
        self.judge = TheJudge()
        self.agents = self.load_all_agents()
        
        # SCAN CONFIGURATION
        self.target_markets = ["futures", "options"] # Can add "spot"
        self.min_volume_24h = 100000 # Ignore dead coins
        self.batch_size = 5 # Process 5 symbols at a time to respect rate limits

    def load_all_agents(self):
        """
        Dynamically load ALL agents found in src/agents folder.
        No more manual list!
        """
        agents = []
        package_path = "src/agents"
        
        # Iterate over all files in src/agents
        for _, name, _ in pkgutil.iter_modules([package_path]):
            if name == "base_agent" or name == "main_brain": continue
            
            try:
                # Import the module
                module = importlib.import_module(f"src.agents.{name}")
                # Find the class that inherits from BaseAgent
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if isinstance(attribute, type) and attribute_name.endswith("Agent") and attribute_name != "BaseAgent":
                        # Instantiate and add
                        agents.append(attribute())
                        logger.info(f"✅ Loaded Agent: {attribute_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load {name}: {e}")
        
        return agents

    async def get_active_ocean(self):
        """
        Fetch ALL tradable assets from Delta Exchange.
        """
        logger.info("🌊 Scanning the Ocean for opportunities...")
        try:
            response = delta_client.get_products()
            products = response.get('result', [])
            
            opportunities = []
            for p in products:
                # Filter Logic
                if p.get('contract_type') in ["perpetual_futures", "call_options", "put_options"]:
                     # You might want to filter by volume here if available in product list
                     # or we filter later after fetching ticker
                     opportunities.append(p['symbol'])
            
            # Fallback if empty (e.g. API error)
            if not opportunities:
                logger.warning("Ocean scan returned 0 symbols. Using fallback.")
                return ["BTCUSD", "ETHUSD"]

            logger.info(f"🌊 Found {len(opportunities)} active symbols in the ocean.")
            return opportunities
        except Exception as e:
            logger.error(f"Ocean Scan Failed: {e}")
            return ["BTCUSD"] # Fallback

    async def analyze_symbol(self, symbol):
        """
        Run the full Brain cycle on ONE symbol.
        """
        try:
            # 1. Fetch OHLC (Data Foundation)
            history = delta_client.get_history(symbol, resolution="1h", limit=50)
            if 'result' not in history or not history['result']:
                return

            df = pd.DataFrame(history['result'])
            cols = ['open', 'high', 'low', 'close', 'volume']
            for c in cols: 
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c])
            
            if df.empty: return

            current_price = float(df['close'].iloc[-1])

            # 2. Run All Agents (Parallel)
            # Filter agents that might fail if data is insufficient?
            # For now run all.
            agent_tasks = [agent.analyze(symbol, df) for agent in self.agents]
            signals: List[Signal] = await asyncio.gather(*agent_tasks)

            # 3. Main Brain Decision
            final_decision = await self.main_brain.analyze(symbol, signals)

            # 4. Filter: Only Act on High Confidence
            if final_decision.confidence > 0.75 and final_decision.action in ["BUY", "SELL"]:
                logger.info(f"🚀 TRADE FOUND: {symbol} | {final_decision.action} | Conf: {final_decision.confidence}")
                
                # Execute
                await executor.execute_order(
                    symbol=symbol,
                    action=final_decision.action,
                    confidence=final_decision.confidence,
                    current_price=current_price,
                    atr=current_price * 0.02 # distinct ATR logic here
                )
            
            # 5. Save State (for UI)
            self.save_state_for_ui(symbol, current_price, signals, final_decision)

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")

    def save_state_for_ui(self, symbol, price, signals, decision):
        # Save to a specific file per symbol or a master state DB
        # For simplicity, we overwrite state.json (UI will flicker between symbols, 
        # ideally UI should support a dropdown)
        import json
        state = {
            "symbol": symbol,
            "price": price,
            "decision": {
                "action": decision.action,
                "confidence": decision.confidence,
                "reasoning": decision.metadata.get("reasoning", "")
            },
            "signals": [
                {
                    "agent": s.agent_name,
                    "action": s.action,
                    "confidence": s.confidence,
                    "metadata": s.metadata
                } for s in signals
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        try:
            with open("data/state.json", "w") as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    async def start(self):
        self.running = True
        logger.info("🚢 Jarvis Ocean Scanner Started.")
        
        # Connect DB
        await db_manager.connect()

        while self.running:
            # 1. Get List of All Symbols
            ocean_symbols = await self.get_active_ocean()
            
            # 2. Process in Batches (Parallel)
            # We use chunks to avoid hitting API rate limits
            chunk_size = 5
            for i in range(0, len(ocean_symbols), chunk_size):
                batch = ocean_symbols[i:i + chunk_size]
                logger.info(f"Processing batch: {batch}")
                
                tasks = [self.analyze_symbol(sym) for sym in batch]
                await asyncio.gather(*tasks)
                
                await asyncio.sleep(1) # Rate limit breathing room

            # 3. Run The Judge (Self-Learning)
            await self.judge.review_performance()
            
            logger.info("💤 Ocean Scan Complete. Sleeping 5 minutes...")
            await asyncio.sleep(300)

if __name__ == "__main__":
    scanner = JarvisScanner()
    asyncio.run(scanner.start())
