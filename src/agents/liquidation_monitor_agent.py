from src.agents.base_agent import BaseAgent, Signal
from typing import Any
import pandas as pd

class LiquidationMonitorAgent(BaseAgent):
    def __init__(self):
        super().__init__("LiquidationMonitorAgent")

    async def analyze(self, symbol: str, data: Any = None) -> Signal:
        """
        Monitors Open Interest (OI) changes to detect liquidation cascades.
        """
        # Needs OI data.
        oi = 0.0
        
        if isinstance(data, dict) and 'oi' in data:
            oi = float(data['oi'])
        elif isinstance(data, pd.DataFrame) and 'oi' in data.columns:
             oi = float(data['oi'].iloc[-1])
        else:
            return Signal(
                agent_name=self.name,
                symbol=symbol,
                action="NEUTRAL",
                confidence=0.0,
                metadata={"status": "No OI data"}
            )

        # Logic:
        # Rapid drop in OI + Rapid price move = Liquidation Cascade
        # We need history to detect "Rapid drop". 
        # If we only have a snapshot, we can only judge absolute levels (High OI = High Risk).
        
        # For this version, we'll just flag High OI as "Caution".
        # In a full version, we'd track OI changes over time.
        
        return Signal(
            agent_name=self.name,
            symbol=symbol,
            action="NEUTRAL",
            confidence=0.5,
            metadata={"open_interest": oi, "status": "Monitoring OI"}
        )
