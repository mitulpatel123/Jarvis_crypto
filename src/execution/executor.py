import logging
import asyncio
from typing import Dict, Any, Optional
from src.data.delta_client import delta_client
from src.risk.risk_manager import risk_manager

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self):
        self.active_orders = {}

    async def execute_order(self, 
                            symbol: str, 
                            action: str, 
                            confidence: float, 
                            current_price: float, 
                            atr: float) -> Optional[Dict]:
        """
        Execute a trade based on a signal, after passing risk checks.
        """
        try:
            # 1. Get Account Balance
            # Note: Delta API returns balance in 'result' -> 'USDT' usually, need to verify structure
            # For now, let's assume get_balances returns a dict where we can find USDT
            balances = delta_client.get_balances()
            # Mocking balance extraction for now as we need to know exact response structure
            # Assuming 'result' is a list of assets
            usdt_balance = 0.0
            if 'result' in balances:
                for asset in balances['result']:
                    if asset['asset_symbol'] == 'USDT':
                        usdt_balance = float(asset['available_balance'])
                        break
            
            if usdt_balance <= 0:
                logger.error("Insufficient USDT balance.")
                return None

            # 2. Calculate Risk Parameters
            stop_loss_price = risk_manager.get_stop_loss_price(current_price, action, atr)
            quantity = risk_manager.calculate_position_size(usdt_balance, current_price, stop_loss_price)
            
            if quantity <= 0:
                logger.warning("Calculated quantity is 0. Trade skipped.")
                return None

            # 3. Safety Check
            # We need to track daily loss somewhere. For now, assuming 0 or passed in.
            if not risk_manager.check_safety(0.0): # TODO: Connect to real PnL tracker
                return None

            # 4. Place Order (Paper vs Live)
            from src.config.settings import settings
            from src.data.db_manager import db_manager
            import pandas as pd

            # AUTO-PAPER PROTOCOL (Safety First)
            # If confidence is low or market is choppy, force PAPER mode
            effective_mode = settings.TRADING_MODE
            
            if effective_mode == "LIVE":
                if confidence < 0.7:
                    logger.warning(f"⚠️ SAFETY TRIGGER: Confidence {confidence} < 0.7. Downgrading to PAPER mode.")
                    effective_mode = "PAPER"
                # Future: Add Market Regime check here
                # if market_regime == "CHOPPY": effective_mode = "PAPER"

            trade_record = {
                "symbol": symbol,
                "direction": action,
                "entry_price": current_price,
                "quantity": quantity,
                "entry_time": pd.Timestamp.now().isoformat(),
                "status": "OPEN"
            }

            if effective_mode == "LIVE":
                logger.warning(f"🚨 LIVE MODE: Placing REAL {action} order for {quantity} {symbol} @ {current_price}")
                
                # Delta Exchange Order Side: 'buy' or 'sell'
                side = "buy" if action == "BUY" else "sell"
                
                order_params = {
                    "product_id": 27, # BTCUSD ID
                    "size": int(quantity * 10), # Assuming contract size logic
                    "side": side,
                    "order_type": "market_order",
                    "limit_price": str(current_price)
                }
                
                try:
                    response = delta_client.place_order(**order_params)
                    logger.info(f"✅ LIVE Order Response: {response}")
                    # Update trade record with real ID if needed
                except Exception as e:
                    logger.error(f"❌ LIVE Order Failed: {e}")
                    return None
            else:
                logger.info(f"📝 PAPER MODE: Simulating {action} order for {quantity} {symbol} @ {current_price}")
                # No API call

            # Store Trade in DB (for both Paper and Live)
            await db_manager.store_trade(trade_record)
            
            return {"status": "executed", "mode": settings.TRADING_MODE, "quantity": quantity, "sl": stop_loss_price}

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return None

executor = ExecutionEngine()
