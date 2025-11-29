import logging
import numpy as np
from typing import Any
from scipy.signal import find_peaks
from src.agents.base_agent import BaseAgent, Signal

logger = logging.getLogger(__name__)

class PatternRecognitionAgent(BaseAgent):
    def __init__(self):
        super().__init__("PatternRecognitionAgent")

    async def analyze(self, symbol: str, data: Any) -> Signal:
        """
        Identify chart patterns like Double Top/Bottom using peak detection.
        data: DataFrame with 'close' prices.
        """
        try:
            if data is None or data.empty:
                return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0)

            close = data['close'].values
            
            # Find peaks (highs) and troughs (lows)
            peaks, _ = find_peaks(close, distance=5)
            troughs, _ = find_peaks(-close, distance=5)
            
            action = "NEUTRAL"
            confidence = 0.0
            pattern = "None"

            # Double Top Logic
            if len(peaks) >= 2:
                last_peak = close[peaks[-1]]
                prev_peak = close[peaks[-2]]
                if abs(last_peak - prev_peak) / prev_peak < 0.01: # Within 1%
                    action = "SELL"
                    confidence = 0.6
                    pattern = "Double Top"

            # Double Bottom Logic
            if len(troughs) >= 2:
                last_trough = close[troughs[-1]]
                prev_trough = close[troughs[-2]]
                if abs(last_trough - prev_trough) / prev_trough < 0.01:
                    action = "BUY"
                    confidence = 0.6
                    pattern = "Double Bottom"

            return Signal(
                agent_name=self.name,
                symbol=symbol,
                action=action,
                confidence=confidence,
                metadata={"pattern": pattern}
            )

        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0)
