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

        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(close, timeperiod=20)
        bb_width = (upper[-1] - lower[-1]) / middle[-1]

        # ATR (Volatility)
        atr = talib.ATR(data['high'].values, data['low'].values, close, timeperiod=14)[-1]

        # Return Raw Features (No Decision)
        # The Main Brain will decide if RSI 35 is a buy or sell based on context
        return Signal(
            agent_name=self.name,
            symbol=symbol,
            action="ANALYSIS", # Placeholder
            confidence=1.0, # High confidence in the data accuracy
            metadata={
                "rsi": float(rsi),
                "macd": float(current_macd),
                "macd_signal": float(current_signal),
                "macd_hist": float(macdhist[-1]),
                "sma_20": float(sma_20),
                "sma_50": float(sma_50),
                "bb_width": float(bb_width),
                "bb_position": float((current_price - lower[-1]) / (upper[-1] - lower[-1])), # 0=Lower, 1=Upper
                "atr": float(atr),
                "price": float(current_price)
            }
        )
