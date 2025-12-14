#!/usr/bin/env python3
"""
Crypto Data Factory - Main Orchestration Script
24/7 Data Collection for ML Model Training
"""

import sys
import os
import signal
import time
from datetime import datetime
from threading import Thread

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Infrastructure imports
from infrastructure.timescale_db import TimescaleDB
from infrastructure.key_manager import KeyManager
from infrastructure.status_server import StatusServer
from infrastructure.monitoring import MonitoringSystem

# Data Layer imports - REMOVED DeltaExchangeCollector
from data_layer.collectors_binance import (
    BinanceWebSocketCollector, 
    BinanceRESTCollector
)
from data_layer.collectors_deribit import DeribitCollector
from data_layer.collectors_coinglass import CoinGlassCollector

from data_layer.collectors_other import (
    CryptoPanicCollector, 
    AlternativeMeCollector,
    EtherscanCollector,
    AlphaVantageCollector
)
from data_layer.collectors_yfinance import YahooFinanceCollector
from data_layer.feature_calculator import FeatureCalculator

# Global variables
db = None
web_server = None
monitor = None
collectors = []

def graceful_shutdown(signum, frame):
    """Handle graceful shutdown"""
    print("\n🛑 Shutdown signal received...")
    
    # Stop all collectors
    for collector in collectors:
        if hasattr(collector, 'stop'):
            collector.stop()
    
    # Stop database
    if db:
        db.close()
    
    # Stop web server
    if web_server:
        web_server.shutdown()
    
    # Stop monitor
    if monitor:
        monitor.stop()
    
    print("✅ All services stopped")
    sys.exit(0)

def main():
    global db, web_server, monitor, collectors
    
    print("🚀 Starting Crypto Data Factory...")
    start_time = time.time()
    
    # Register shutdown handler
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    try:
        # Initialize configuration
        from config.api_key_parser import APIKeyParser
        parser = APIKeyParser()
        parser.add_proxies_from_file()
        config = parser.parse()

        # Initialize infrastructure
        db = TimescaleDB()
        key_manager = KeyManager(config)
        monitor = MonitoringSystem()
        
        # Initialize collectors
        binance_ws = BinanceWebSocketCollector(symbol="btcusdt", proxy_manager=key_manager)
        binance_rest = BinanceRESTCollector(symbol="BTCUSDT", key_manager=key_manager)
        deribit = DeribitCollector()
        coinglass = CoinGlassCollector()  # NEW: Restored CoinGlass

        cryptopanic = CryptoPanicCollector(key_manager)
        alternative_me = AlternativeMeCollector()
        etherscan = EtherscanCollector(key_manager)
        alpha_vantage = AlphaVantageCollector(key_manager)
        yfinance = YahooFinanceCollector()
        
        # Store collectors for shutdown
        collectors = [
            binance_ws, binance_rest, deribit, coinglass,
            cryptopanic, alternative_me, etherscan, alpha_vantage, yfinance
        ]
        
        # Start Binance WebSocket threads
        t_ws = Thread(target=binance_ws.run, daemon=True)
        t_ws.start()
        
        # Start Liquidation stream
        t_liq = Thread(target=binance_ws.run_liquidation_stream, daemon=True)
        t_liq.start()
        
        # Start other collectors
        deribit.start()
        coinglass.start()

        cryptopanic.start()
        alternative_me.start()
        etherscan.start()
        alpha_vantage.start()
        yfinance.start()
        
        # Initialize feature calculator
        feature_calc = FeatureCalculator()
        
        # Start web server with live collectors
        web_server = StatusServer(
            collectors=collectors,
            db=db,
            monitor=monitor,
            port=8090
        )
        web_server_thread = Thread(target=web_server.run, daemon=True)
        web_server_thread.start()
        
        print(f"✅ Factory initialized in {time.time() - start_time:.2f}s")
        print("📊 Starting data collection loop...")
        
        # Main collection loop
        while True:
            loop_start = time.time()
            
            # Get snapshots from all collectors
            binance_data = binance_ws.get_snapshot()
            binance_rest_data = binance_rest.get_snapshot()
            deribit_data = deribit.get_snapshot()
            coinglass_data = coinglass.get_snapshot()

            cryptopanic_data = cryptopanic.get_snapshot()
            alternative_me_data = alternative_me.get_snapshot()
            etherscan_data = etherscan.get_snapshot()
            alpha_vantage_data = alpha_vantage.get_snapshot()
            yfinance_data = yfinance.get_snapshot()
            
            # Combine all data
            combined_data = {
                **binance_data,
                **binance_rest_data,
                **deribit_data,
                **coinglass_data,
                **cryptopanic_data,
                **alternative_me_data,
                **etherscan_data,
                **alpha_vantage_data,
                **yfinance_data
            }
            
            # Calculate derived features
            derived_features = feature_calc.calculate_features(combined_data)
            
            # Merge all data
            final_data = {**combined_data, **derived_features}
            
            # Insert into database
            timestamp = datetime.utcnow()
            symbol = "BTCUSDT"
            final_data['timestamp'] = timestamp
            final_data['symbol'] = symbol
            db.insert_single(final_data)
            
            # Monitor update handled in DB class internally
            
            # Maintain 1-second interval
            loop_duration = time.time() - loop_start
            sleep_time = max(0, 1.0 - loop_duration)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print("\n🛑 Manual interruption received...")
        graceful_shutdown(None, None)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()