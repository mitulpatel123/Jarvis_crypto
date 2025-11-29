import talib
import pandas as pd
from src.agents.base_agent import BaseAgent, Signal

class TrendFollowingAgent(BaseAgent):
    def __init__(self):
        super().__init__("TrendFollowingAgent")

    async def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        """
        Analyze trend using ADX and EMA.
        """
        if data.empty or len(data) < 30:
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0)

        high = data['high'].values
        low = data['low'].values
        close = data['close'].values

        # ADX
        adx = talib.ADX(high, low, close, timeperiod=14)[-1]
        
        # EMA
        ema_short = talib.EMA(close, timeperiod=12)[-1]
        ema_long = talib.EMA(close, timeperiod=26)[-1]

        action = "NEUTRAL"
        confidence = 0.0

        # Strong Trend
        if adx > 25:
            if ema_short > ema_long:
                action = "BUY"
                confidence = 0.6 + (min(adx, 50) / 100) # Higher ADX = Higher confidence
            elif ema_short < ema_long:
                action = "SELL"
                confidence = 0.6 + (min(adx, 50) / 100)
        
        return Signal(
            agent_name=self.name,
            symbol=symbol,
            action=action,
            confidence=min(confidence, 1.0),
            metadata={"adx": float(adx), "ema_short": float(ema_short), "ema_long": float(ema_long)}
        )
