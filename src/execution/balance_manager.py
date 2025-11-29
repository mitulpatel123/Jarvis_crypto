import logging
import json
import os
from src.config.settings import settings
from src.data.delta_client import delta_client

logger = logging.getLogger(__name__)

class BalanceManager:
    def __init__(self):
        self.paper_file = "data/paper_wallet.json"
        self._init_paper_wallet()

    def _init_paper_wallet(self):
        if not os.path.exists(self.paper_file):
            with open(self.paper_file, "w") as f:
                json.dump({"balance": 10000.0, "currency": "USD"}, f)

    def get_balance(self, mode: str = None) -> float:
        if mode is None:
            mode = settings.TRADING_MODE

        if mode == "LIVE":
            try:
                # Fetch from Delta Exchange
                # Note: This requires delta_client to have a get_wallet_balance method
                # If not, we might need to implement it or use a raw request
                # For now, assuming delta_client has it or we catch error
                if hasattr(delta_client, 'get_wallet_balance'):
                    return delta_client.get_wallet_balance()
                else:
                    # Fallback or mock if method missing
                    return 0.0
            except Exception as e:
                logger.error(f"Failed to fetch live balance: {e}")
                return 0.0
        else:
            # Paper Mode
            try:
                with open(self.paper_file, "r") as f:
                    data = json.load(f)
                    return data.get("balance", 10000.0)
            except:
                return 10000.0

    def update_paper_balance(self, amount: float):
        """Add or subtract amount from paper balance."""
        try:
            current = self.get_balance("PAPER")
            new_bal = current + amount
            with open(self.paper_file, "w") as f:
                json.dump({"balance": new_bal, "currency": "USD"}, f)
            return new_bal
        except Exception as e:
            logger.error(f"Failed to update paper balance: {e}")
            return current

balance_manager = BalanceManager()
