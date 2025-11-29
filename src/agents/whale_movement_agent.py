from src.agents.base_agent import BaseAgent, Signal

class WhaleMovementAgent(BaseAgent):
    def __init__(self):
        super().__init__("WhaleMovementAgent")

    async def analyze(self, symbol: str, data: object = None) -> Signal:
        # Detect Volume Anomalies (Whales)
        if data is None or data.empty: return Signal(self.name, symbol, "NEUTRAL", 0.0)
        
        # Calculate Volume Moving Average
        vol_sma = data['volume'].rolling(20).mean().iloc[-1]
        curr_vol = data['volume'].iloc[-1]
        
        # If volume is 300% of normal, a Whale entered
        if curr_vol > 3.0 * vol_sma:
            price_change = data['close'].iloc[-1] - data['open'].iloc[-1]
            action = "BUY" if price_change > 0 else "SELL"
            return Signal(self.name, symbol, action, 0.95, {"reason": "Whale Volume Spike"})
            
        return Signal(self.name, symbol, "NEUTRAL", 0.1, {"reason": "Normal Volume"})
