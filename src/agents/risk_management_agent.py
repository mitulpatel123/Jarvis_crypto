from src.agents.base_agent import BaseAgent, Signal
from typing import Any

class RiskManagementAgent(BaseAgent):
    def __init__(self):
        super().__init__("RiskManagementAgent")

    async def analyze(self, symbol: str, data: Any = None) -> Signal:
        # Basic Risk Check: High Volatility = Reduce Size
        try:
            if data is None or data.empty:
                return Signal(self.name, symbol, "NEUTRAL", 0.0, {"status": "No Data"})
            
            # Calculate ATR-like volatility (High - Low)
            high_low = (data['high'] - data['low']) / data['close']
            avg_volatility = high_low.rolling(14).mean().iloc[-1]
            
            if avg_volatility > 0.05: # >5% daily move is risky
                return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=1.0, metadata={"risk": "HIGH_VOLATILITY", "advice": "Reduce Position Size"})
            
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0, metadata={"risk": "NORMAL", "status": "Safe to Trade"})
        except Exception as e:
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0, metadata={"error": str(e)})
