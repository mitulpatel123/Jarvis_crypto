from src.agents.base_agent import BaseAgent, Signal
from typing import Any

class WhaleMovementAgent(BaseAgent):
    def __init__(self):
        super().__init__("WhaleMovementAgent")

    async def analyze(self, symbol: str, data: Any = None) -> Signal:
        # Heuristic: Large Volume Spike = Whale Activity
        try:
            if data is None or data.empty:
                return Signal(self.name, symbol, "NEUTRAL", 0.0, {"error": "No data"})
            
            # Calculate average volume
            avg_vol = data['volume'].rolling(20).mean().iloc[-1]
            curr_vol = data['volume'].iloc[-1]
            
            if curr_vol > 2.5 * avg_vol:
                # Huge spike
                price_change = data['close'].iloc[-1] - data['open'].iloc[-1]
                action = "BUY" if price_change > 0 else "SELL"
                return Signal(self.name, symbol, action, 0.8, {"reason": "Huge Volume Spike (Whale)", "vol_mult": float(curr_vol/avg_vol)})
            
            return Signal(self.name, symbol, "NEUTRAL", 0.0, {"status": "Normal Volume"})
        except Exception as e:
            return Signal(self.name, symbol, "NEUTRAL", 0.0, {"error": str(e)})
