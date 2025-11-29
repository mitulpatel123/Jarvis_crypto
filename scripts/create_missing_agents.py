import os
import sys

# List of missing agents from prompt2.md
missing_agents = [
    "whale_movement_agent",
    "options_flow_agent",
    "exchange_inflow_agent",
    "liquidation_monitor_agent",
    "order_book_agent",
    "funding_rate_agent",
    "spread_agent",
    "session_agent",
    "gas_fee_agent",
    "smart_money_agent",
    "staking_agent",
    "risk_management_agent",
    "market_regime_agent",
    "anomaly_detection_agent",
    "position_sizing_agent",
    "stop_loss_optimizer",
    "entry_sniper_agent",
    "cross_exchange_arbitrage",
    "economic_calendar_agent",
    "sentiment_aggregation_agent",
    "volatility_smile_agent",
    "mean_reversion_agent"
]

template = """from src.agents.base_agent import BaseAgent, Signal
from typing import Any

class {class_name}(BaseAgent):
    def __init__(self):
        super().__init__("{agent_name}")

    async def analyze(self, symbol: str, data: Any = None) -> Signal:
        # Placeholder logic for God Mode expansion
        return Signal(
            agent_name=self.name,
            symbol=symbol,
            action="NEUTRAL",
            confidence=0.0,
            metadata={{"status": "Not implemented yet"}}
        )
"""

def to_camel_case(snake_str):
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)

def main():
    base_dir = "src/agents"
    os.makedirs(base_dir, exist_ok=True)
    
    for agent_file in missing_agents:
        class_name = to_camel_case(agent_file)
        agent_name = class_name
        
        content = template.format(class_name=class_name, agent_name=agent_name)
        
        file_path = os.path.join(base_dir, f"{agent_file}.py")
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write(content)
            print(f"Created {file_path}")
        else:
            print(f"Skipped {file_path} (already exists)")

if __name__ == "__main__":
    main()
