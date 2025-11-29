import logging
from typing import Optional, Dict
import pandas as pd
from datetime import datetime
from src.data.delta_client import delta_client
from src.data.db_manager import db_manager

logger = logging.getLogger(__name__)

class ExecutionEngine:
    async def execute_order(self, symbol, action, confidence, current_price, atr, mode, timestamp=None):
        """
        Executes order based on Mode:
        - BACKTEST: Log to DB with historical timestamp.
        - PAPER: Log to DB with current timestamp (No API).
        - LIVE: Call Delta API + Log to DB.
        """
        quantity = 100 # Simplification for example
        entry_time = timestamp if timestamp else datetime.now()

        trade_record = {
            "symbol": symbol,
            "direction": action,
            "mode": mode,
            "entry_price": current_price,
            "quantity": quantity,
            "entry_time": entry_time,
            "status": "OPEN",
            "profit_loss": 0.0
        }

        if mode == "LIVE":
            # REAL MONEY DANGER ZONE
            try:
                side = "buy" if action == "BUY" else "sell"
                response = delta_client.place_order(
                    symbol=symbol, 
                    side=side, 
                    order_type="market_order", 
                    quantity=quantity
                )
                logger.warning(f"🚨 LIVE TRADE EXECUTED: {response}")
            except Exception as e:
                logger.error(f"❌ Live Trade Failed: {e}")
                return

        elif mode == "PAPER":
            logger.info(f"📝 PAPER TRADE: {action} {symbol} @ {current_price}")

        elif mode == "BACKTEST":
            # Silent logging for speed
            pass

        # Save to Database (The Source of Truth for UI)
        await db_manager.store_trade(trade_record)

executor = ExecutionEngine()
