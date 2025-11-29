import asyncio
import logging
import sys
from src.execution.executor import executor
from src.risk.risk_manager import risk_manager

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

async def main():
    symbol = "BTCUSD"
    print(f"--- Verifying Execution Engine (Dry Run) for {symbol} ---")

    # 1. Test Risk Manager Math
    print("\n[1] Testing Risk Manager Math...")
    balance = 1000.0
    entry = 50000.0
    sl = 49500.0 # 500 diff
    
    # Risk 1% = $10
    # Qty = 10 / 500 = 0.02 BTC
    qty = risk_manager.calculate_position_size(balance, entry, sl)
    print(f"Balance: ${balance}, Entry: ${entry}, SL: ${sl}")
    print(f"Calculated Qty: {qty} (Expected ~0.02)")
    
    if qty == 0.02:
        print("✅ Risk Math Correct")
    else:
        print(f"❌ Risk Math Incorrect: {qty}")

    # 2. Test Execution Engine (Simulated)
    print("\n[2] Testing Execution Engine (Simulated)...")
    
    # Mocking Delta Client balance in executor is hard without dependency injection or mocking lib.
    # But executor.execute_order calls delta_client.get_balances()
    # We can try to run it. If it fails due to API, we know connectivity is the issue.
    # If it returns None (insufficient balance or error), we'll see logs.
    
    # Note: This will attempt to fetch REAL balance.
    # If balance is 0, it will return None.
    
    try:
        # Using a very wide SL to ensure small size if balance is low
        # But we need current price.
        current_price = 90000.0
        atr = 1000.0
        
        result = await executor.execute_order(
            symbol=symbol,
            action="BUY",
            confidence=0.8,
            current_price=current_price,
            atr=atr
        )
        
        if result:
            print(f"✅ Execution Success (Simulated): {result}")
        else:
            print("⚠️ Execution Returned None (Check logs for 'Insufficient balance' or errors)")

    except Exception as e:
        print(f"❌ Execution Failed: {e}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
