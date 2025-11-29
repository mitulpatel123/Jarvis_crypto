from src.agents.base_agent import BaseAgent, Signal
import pandas as pd
import numpy as np

class VolatilityAgent(BaseAgent):
    def __init__(self):
        super().__init__("VolatilityAgent")

    async def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        if data is None or data.empty: return Signal(self.name, symbol, "NEUTRAL", 0.0)
        
        # ATR Calculation
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]
        
        current_vol = true_range.iloc[-1]
        
        # Logic: High Volatility = High Risk but High Reward potential
        if current_vol > 2 * atr:
            return Signal(self.name, symbol, "NEUTRAL", 0.9, {"status": "High Volatility", "atr": float(atr)})
        elif current_vol < 0.5 * atr:
            return Signal(self.name, symbol, "ANALYSIS", 0.8, {"status": "Squeeze (Breakout Soon)", "atr": float(atr)})
            
        return Signal(self.name, symbol, "NEUTRAL", 0.5, {"atr": float(atr)})
