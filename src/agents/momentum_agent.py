import logging
import talib
from typing import Any
from src.agents.base_agent import BaseAgent, Signal

logger = logging.getLogger(__name__)

class MomentumAgent(BaseAgent):
    def __init__(self):
        super().__init__("MomentumAgent")

    async def analyze(self, symbol: str, data: Any) -> Signal:
        """
        Analyze momentum using Stochastic Oscillator and ROC.
        """
        try:
            if data is None or data.empty:
                return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0)

            high = data['high'].values
            low = data['low'].values
            close = data['close'].values

            # Stochastic
            slowk, slowd = talib.STOCH(high, low, close)
            
            # ROC
            roc = talib.ROC(close, timeperiod=10)
            
            action = "NEUTRAL"
            confidence = 0.0
            
            current_k = slowk[-1]
            current_d = slowd[-1]
            current_roc = roc[-1]

            # Logic
            if current_k < 20 and current_d < 20 and current_k > current_d:
                # Oversold crossover
                if current_roc > 0:
                    action = "BUY"
                    confidence = 0.7
            elif current_k > 80 and current_d > 80 and current_k < current_d:
                # Overbought crossover
                if current_roc < 0:
                    action = "SELL"
                    confidence = 0.7

            return Signal(
                agent_name=self.name,
                symbol=symbol,
                action=action,
                confidence=confidence,
                metadata={"stoch_k": current_k, "roc": current_roc}
            )

        except Exception as e:
            logger.error(f"Momentum analysis failed: {e}")
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0)
