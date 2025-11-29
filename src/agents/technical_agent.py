import talib
import pandas as pd
import numpy as np
from src.agents.base_agent import BaseAgent, Signal

class TechnicalAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("TechnicalAnalysisAgent")

    async def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        """
        Analyze technical indicators: RSI, MACD, SMA.
        data: DataFrame with 'close' column.
        """
        if data.empty or len(data) < 30:
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0)

        close = data['close'].values

        # RSI
        rsi = talib.RSI(close, timeperiod=14)[-1]

        # MACD
        macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        current_macd = macd[-1]
        current_signal = macdsignal[-1]

        # SMA
        sma_20 = talib.SMA(close, timeperiod=20)[-1]
        sma_50 = talib.SMA(close, timeperiod=50)[-1]
        current_price = close[-1]

        # Logic
        score = 0
        
        # RSI Logic
        if rsi < 30:
            score += 1  # Oversold -> Buy
        elif rsi > 70:
            score -= 1  # Overbought -> Sell

        # MACD Logic
        if current_macd > current_signal:
            score += 1
        else:
            score -= 1

        # SMA Logic
        if current_price > sma_20 > sma_50:
            score += 1
        elif current_price < sma_20 < sma_50:
            score -= 1

        # Determine Signal
        action = "NEUTRAL"
        confidence = 0.5
        
        if score >= 2:
            action = "BUY"
            confidence = 0.7 + (0.1 * (score - 2))
        elif score <= -2:
            action = "SELL"
            confidence = 0.7 + (0.1 * (abs(score) - 2))

        return Signal(
            agent_name=self.name,
            symbol=symbol,
            action=action,
            confidence=min(confidence, 1.0),
            metadata={
                "rsi": float(rsi),
                "macd": float(current_macd),
                "sma_20": float(sma_20),
                "score": score
            }
        )
