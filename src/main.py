import asyncio
import logging
import sys
import pandas as pd
from typing import List

# Configure logging
logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.data.delta_client import delta_client
from src.data.groq_client import groq_client
from src.agents.base_agent import Signal
from src.agents.technical_agent import TechnicalAnalysisAgent
from src.agents.trend_agent import TrendFollowingAgent
from src.agents.volatility_agent import VolatilityAgent
from src.agents.volume_agent import VolumeAnalysisAgent
from src.agents.news_agent import NewsSentimentAgent
from src.agents.pattern_agent import PatternRecognitionAgent
from src.agents.momentum_agent import MomentumAgent
from src.agents.main_brain import MainBrain
from src.execution.executor import executor

class JarvisTrader:
    def __init__(self):
        self.symbol = "BTCUSD"
        self.running = False
        
        # Initialize Agents
        self.agents = [
            TechnicalAnalysisAgent(),
            TrendFollowingAgent(),
            VolatilityAgent(),
            VolumeAnalysisAgent(),
            NewsSentimentAgent(),
            PatternRecognitionAgent(),
            MomentumAgent()
        ]
        self.main_brain = MainBrain()

    async def run_cycle(self):
        """
        Execute one full trading cycle.
        """
        logger.info(f"--- Starting Trading Cycle for {self.symbol} ---")
        
        try:
            # 1. Fetch Data
            # Fetch OHLC for technical agents
            history = delta_client.get_history(self.symbol, resolution="1h", limit=50)
            if 'result' not in history:
                logger.error("Failed to fetch OHLC data.")
                return
            
            candles = history['result']
            df = pd.DataFrame(candles)
            cols = ['open', 'high', 'low', 'close', 'volume']
            for c in cols:
                df[c] = pd.to_numeric(df[c])
            
            current_price = df['close'].iloc[-1]
            
            # Calculate ATR for Risk Manager (using Volatility Agent logic or direct TA-Lib)
            # We can extract it from Volatility Agent signal metadata if available, 
            # or just calculate it here for safety.
            # For now, let's rely on Volatility Agent to pass it in metadata.

            # 2. Run Agents (Parallel)
            logger.info("Running Agents...")
            agent_tasks = []
            for agent in self.agents:
                # Some agents need DF, some (News) need just symbol
                # We'll pass DF to all, BaseAgent handles it? 
                # NewsAgent signature is (symbol, data=None).
                # Technical agents expect data.
                agent_tasks.append(agent.analyze(self.symbol, df))
            
            signals: List[Signal] = await asyncio.gather(*agent_tasks)
            
            # Log Signals
            for s in signals:
                logger.info(f"Signal: {s.agent_name} -> {s.action} ({s.confidence})")

            # 3. Main Brain Decision
            logger.info("Consulting Main Brain...")
            final_decision = await self.main_brain.analyze(self.symbol, signals)
            logger.info(f"🏆 Final Decision: {final_decision.action} ({final_decision.confidence})")
            logger.info(f"📝 Reasoning: {final_decision.metadata.get('reasoning')}")

            # 4. Execution
            if final_decision.action in ["BUY", "SELL"]:
                # Extract ATR for SL calculation
                # Find VolatilityAgent signal
                vol_sig = next((s for s in signals if s.agent_name == "VolatilityAgent"), None)
                atr = vol_sig.metadata.get('atr', 0.0) if vol_sig else 0.0
                
                # If ATR missing, calculate simple fallback?
                if atr == 0.0:
                    # Simple fallback: 1% of price
                    atr = current_price * 0.01
                
                result = await executor.execute_order(
                    symbol=self.symbol,
                    action=final_decision.action,
                    confidence=final_decision.confidence,
                    current_price=current_price,
                    atr=atr
                )
                
                if result:
                    logger.info(f"✅ Trade Executed: {result}")
                else:
                    logger.warning("⚠️ Trade Skipped (Risk/Safety)")
            else:
                logger.info("No trade action taken.")
            # 5. Export State for Dashboard
            state = {
                "symbol": self.symbol,
                "price": current_price,
                "signals": [
                    {
                        "agent": s.agent_name,
                        "action": s.action,
                        "confidence": s.confidence,
                        "metadata": s.metadata
                    } for s in signals
                ],
                "decision": {
                    "action": final_decision.action,
                    "confidence": final_decision.confidence,
                    "reasoning": final_decision.metadata.get('reasoning')
                },
                "last_update": pd.Timestamp.now().isoformat()
            }
            
            import json
            import os
            os.makedirs("data", exist_ok=True)
            with open("data/state.json", "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Cycle failed: {e}")

    async def start(self):
        """
        Start the main loop.
        """
        self.running = True
        logger.info("Jarvis Trader Started.")
        while self.running:
            await self.run_cycle()
            


            # Sleep for 1 hour (or configurable interval)
            logger.info("Sleeping for 1 hour...")
            await asyncio.sleep(3600)

if __name__ == "__main__":
    jarvis = JarvisTrader()
    asyncio.run(jarvis.start())
