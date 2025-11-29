import json
import logging
import asyncio
from typing import Dict
from datetime import datetime, timedelta
from src.data.db_manager import db_manager
import os

logger = logging.getLogger("Judge")

class TheJudge:
    def __init__(self, weights_path="src/config/agent_weights.json"):
        self.weights_path = weights_path
        self.default_weight = 1.0
        self.learning_rate = 0.1  # How fast we adapt (0.1 = 10% change per review)
        os.makedirs(os.path.dirname(self.weights_path), exist_ok=True)

    async def review_performance(self):
        """
        The 'Nightly Review':
        1. Fetch all trades closed in the last 24h.
        2. Fetch what each agent 'voted' for those specific timestamps.
        3. Reward the agents who voted correctly.
        4. Punish the agents who voted incorrectly.
        """
        logger.info("👨‍⚖️ The Judge is entering the courtroom...")
        
        # 1. Get recent closed trades
        trades = await db_manager.get_recent_trades(limit=50)
        if not trades:
            logger.info("No trades to review. Court adjourned.")
            return

        # Load current weights
        current_weights = self.load_weights()

        for trade in trades:
            outcome = trade['profit_loss']  # Positive or Negative
            entry_time = trade['entry_time']
            
            # 2. Get the specific "Brain Scan" at the moment of entry
            agent_votes = await db_manager.get_agent_signals_at_time(entry_time)
            
            for agent_name, signal in agent_votes.items():
                if agent_name not in current_weights:
                    current_weights[agent_name] = self.default_weight

                # Logic: Did the agent agree with the winning trade?
                
                # CASE A: Trade WON
                if outcome > 0:
                    if signal == trade['direction']: # Agent said BUY and we WON
                        current_weights[agent_name] += self.learning_rate
                    elif signal != "NEUTRAL": # Agent said SELL but we WON (Wrong!)
                        current_weights[agent_name] -= self.learning_rate

                # CASE B: Trade LOST
                elif outcome < 0:
                    if signal == trade['direction']: # Agent said BUY and we LOST (Wrong!)
                        current_weights[agent_name] -= self.learning_rate
                    elif signal != "NEUTRAL": # Agent said SELL (saved us, technically)
                        current_weights[agent_name] += (self.learning_rate * 0.5)

        # Normalize weights (keep them between 0.1 and 2.0)
        for agent in current_weights:
            current_weights[agent] = max(0.1, min(current_weights[agent], 2.0))

        # 3. Save the new "Brain Configuration"
        self.save_weights(current_weights)
        logger.info("⚖️ Verdict delivered. Agent weights updated.")

    def load_weights(self) -> Dict[str, float]:
        try:
            with open(self.weights_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_weights(self, weights: Dict[str, float]):
        with open(self.weights_path, 'w') as f:
            json.dump(weights, f, indent=4)

# Usage
if __name__ == "__main__":
    judge = TheJudge()
    asyncio.run(judge.review_performance())
