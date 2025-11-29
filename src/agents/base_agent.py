from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel

class Signal(BaseModel):
    agent_name: str
    symbol: str
    action: str  # 'BUY', 'SELL', 'NEUTRAL'
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = {}

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def analyze(self, symbol: str, data: Any) -> Signal:
        """
        Analyze the given data for the symbol and return a trading signal.
        data: Can be a DataFrame of OHLC, or other relevant data.
        """
        pass
