import talib
import pandas as pd
from src.agents.base_agent import BaseAgent, Signal

class VolatilityAgent(BaseAgent):
    def __init__(self):
        super().__init__("VolatilityAgent")

    async def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        """
        Analyze volatility using ATR and Bollinger Bands.
        """
        if data.empty or len(data) < 30:
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0)

        high = data['high'].values
        low = data['low'].values
        close = data['close'].values

        # ATR
        atr = talib.ATR(high, low, close, timeperiod=14)[-1]
        
        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        
        current_price = close[-1]
        band_width = (upper[-1] - lower[-1]) / middle[-1]

        action = "NEUTRAL"
        confidence = 0.5
        
        # High Volatility Logic (Expansion)
        if band_width > 0.05: # Arbitrary threshold for "high volatility"
            # If price is near bands, it might mean breakout or reversal
            if current_price > upper[-1]:
                action = "BUY" # Breakout
                confidence = 0.7
            elif current_price < lower[-1]:
                action = "SELL" # Breakdown
                confidence = 0.7
        else:
            # Low Volatility (Squeeze)
            confidence = 0.3 # Wait for breakout

        return Signal(
            agent_name=self.name,
            symbol=symbol,
            action=action,
            confidence=confidence,
            metadata={"atr": float(atr), "band_width": float(band_width)}
        )
