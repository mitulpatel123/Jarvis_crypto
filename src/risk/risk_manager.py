import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.risk_per_trade = 0.01  # 1% risk per trade
        self.max_daily_loss = 0.05  # 5% max daily loss
        self.max_leverage = 1.0     # 1x leverage (Conservative)
        self.daily_loss = 0.0       # Tracked daily loss

    def calculate_position_size(self, 
                                account_balance: float, 
                                entry_price: float, 
                                stop_loss_price: float) -> float:
        """
        Calculate position size based on risk per trade.
        Formula: Quantity = (Risk Amount) / (Entry - SL)
        """
        try:
            if account_balance <= 0:
                logger.warning("Account balance is zero or negative.")
                return 0.0

            risk_amount = account_balance * self.risk_per_trade
            price_diff = abs(entry_price - stop_loss_price)
            
            if price_diff == 0:
                logger.warning("Stop Loss is same as Entry Price. Cannot calculate size.")
                return 0.0

            # Quantity in base asset (e.g., BTC)
            quantity = risk_amount / price_diff
            
            # Leverage Check
            notional_value = quantity * entry_price
            max_notional = account_balance * self.max_leverage
            
            if notional_value > max_notional:
                logger.info(f"Position size {quantity} exceeds max leverage. Capping at 1x.")
                quantity = max_notional / entry_price

            return round(quantity, 6) # Round to reasonable decimals

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0

    def check_safety(self, current_daily_loss: float) -> bool:
        """
        Check if trading should proceed based on daily loss limits.
        """
        if current_daily_loss >= self.max_daily_loss:
            logger.critical(f"Daily loss limit hit ({current_daily_loss*100}%). Trading Halted.")
            return False
        return True

    def get_stop_loss_price(self, entry_price: float, action: str, atr: float) -> float:
        """
        Calculate Stop Loss price based on ATR.
        """
        multiplier = 2.0
        if action == "BUY":
            return entry_price - (atr * multiplier)
        elif action == "SELL":
            return entry_price + (atr * multiplier)
        return 0.0

risk_manager = RiskManager()
