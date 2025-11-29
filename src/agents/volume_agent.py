import talib
import pandas as pd
import numpy as np
from src.agents.base_agent import BaseAgent, Signal

class VolumeAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("VolumeAnalysisAgent")

    async def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        """
        Analyze volume patterns.
        """
        if data.empty or len(data) < 30:
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0)

        close = data['close'].values
        volume = data['volume'].values.astype(float)

        # OBV
        obv = talib.OBV(close, volume)[-1]
        
        # Volume SMA
        vol_sma = talib.SMA(volume, timeperiod=20)[-1]
        current_vol = volume[-1]

        action = "NEUTRAL"
        confidence = 0.5

        # Volume Spike
        if current_vol > 2 * vol_sma:
            # High volume
            if close[-1] > close[-2]:
                action = "BUY" # High volume up-move
                confidence = 0.8
            else:
                action = "SELL" # High volume down-move
                confidence = 0.8
        
        return Signal(
            agent_name=self.name,
            symbol=symbol,
            action=action,
            confidence=confidence,
            metadata={"obv": float(obv), "vol_ratio": float(current_vol / vol_sma if vol_sma else 0)}
        )
