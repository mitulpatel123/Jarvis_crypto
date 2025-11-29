from src.agents.base_agent import BaseAgent, Signal
from typing import Any
import pandas as pd

class FundingRateAgent(BaseAgent):
    def __init__(self):
        super().__init__("FundingRateAgent")

    async def analyze(self, symbol: str, data: Any = None) -> Signal:
        """
        Analyzes funding rates to detect potential squeezes.
        Expects 'data' to contain ticker info with funding rate, or fetches it.
        """
        # In a real scenario, we'd want the current ticker info, not just OHLC
        # Assuming 'data' might be a DataFrame (OHLC) or a dict (Ticker)
        # If it's OHLC, we can't get funding rate easily unless it's in the columns.
        # So we'll try to fetch it if missing, or return Neutral.
        
        funding_rate = 0.0
        
        # Check if we have ticker data passed in metadata or separate call
        # For now, let's assume the MainBrain or Scanner passes a dictionary with 'funding_rate'
        # OR we fetch it here (but async inside async might be tricky if client isn't async)
        # Let's assume we use the DeltaClient synchronously here for now, or skip if not available.
        
        # To avoid blocking, we'll check if 'data' has it.
        if isinstance(data, dict) and 'funding_rate' in data:
            funding_rate = float(data['funding_rate'])
        elif isinstance(data, pd.DataFrame) and 'funding_rate' in data.columns:
             funding_rate = float(data['funding_rate'].iloc[-1])
        else:
            # Fallback: We can't analyze without data.
            # In "God Mode", the scanner should fetch Ticker data too.
            return Signal(
                agent_name=self.name,
                symbol=symbol,
                action="NEUTRAL",
                confidence=0.0,
                metadata={"status": "No funding data"}
            )

        # Logic:
        # High Positive Funding (> 0.01% per hour) -> Longs paying Shorts -> Overcrowded Longs -> Bearish (Long Squeeze Risk)
        # High Negative Funding (< -0.01%) -> Shorts paying Longs -> Overcrowded Shorts -> Bullish (Short Squeeze Risk)
        
        threshold = 0.0001 # 0.01%
        
        if funding_rate > threshold * 5: # Extreme Positive
            return Signal(
                agent_name=self.name,
                symbol=symbol,
                action="SELL",
                confidence=0.8,
                metadata={"reason": "Extreme Positive Funding (Long Squeeze Risk)", "rate": funding_rate}
            )
        elif funding_rate < -threshold * 5: # Extreme Negative
            return Signal(
                agent_name=self.name,
                symbol=symbol,
                action="BUY",
                confidence=0.8,
                metadata={"reason": "Extreme Negative Funding (Short Squeeze Risk)", "rate": funding_rate}
            )
            
        return Signal(
            agent_name=self.name,
            symbol=symbol,
            action="NEUTRAL",
            confidence=0.1,
            metadata={"rate": funding_rate}
        )
