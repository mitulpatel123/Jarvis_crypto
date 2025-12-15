"""
Deribit Data Collector
Fetches implied volatility and greeks.
Refactored to use ATM Options for Greeks as Perpetuals do not have them.
"""

import requests
import time
import threading
import math
import numpy as np
from scipy.stats import norm
from typing import Dict, Any, Optional
from datetime import datetime

# Monitor hooks (optional)
try:
    from infrastructure.monitoring import MONITOR
except ImportError:
    MONITOR = None

class DeribitCollector(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = False
        self.lock = threading.Lock()
        
        self.base_url = "https://www.deribit.com/api/v2/public"
        self.latest_data = {
            "implied_volatility": 0.0,
            "iv_rank": 50.0,
            "delta_exposure": 0.0,
            "gamma_exposure": 0.0, # Not actively used but good to have
            "theta": 0.0,
            "vega": 0.0,
            "put_call_ratio_vol": 0.0,
            "put_call_ratio_oi": 0.0,
            "delta_bs": 0.0,
            "gamma_bs": 0.0,
            "vega_bs": 0.0,
            "theta_bs": 0.0,
            # Reserve fields for Gamma Strikes
            "gamma_strike_1": 0.0,
            "gamma_strike_2": 0.0,
            "gamma_strike_3": 0.0,
            # Backup fields for Binance
            "backup_funding_rate": 0.0,
            "backup_open_interest": 0.0
        }
        print("✅ DeribitCollector (ATM Greeks) initialized")

    def run(self):
        """Main loop"""
        self.running = True
        while self.running:
            self.get_latest_data()
            time.sleep(10) # 10s interval

    def fetch_atm_option_greeks(self):
        """
        Fetch Greeks from the nearest At-The-Money (ATM) Option.
        Perpetuals don't have Greeks, so we use the ATM option as a proxy for market volatility/risk.
        """
        try:
            # 1. Get Index Price
            idx_resp = requests.get(f"{self.base_url}/get_index_price", params={"index_name": "btc_usd"}, timeout=5)
            if idx_resp.status_code != 200:
                print(f"⚠️ Deribit: Failed to get index price {idx_resp.status_code}")
                return
            
            btc_price = idx_resp.json()['result']['index_price']
            
            # 2. Find closest strike (Round to nearest 1000)
            target_strike = round(btc_price / 1000) * 1000
            
            # 3. Get Option Chain Summary
            book_url = f"{self.base_url}/get_book_summary_by_currency"
            params = {"currency": "BTC", "kind": "option"}
            book_resp = requests.get(book_url, params=params, timeout=5)
            
            if book_resp.status_code == 200:
                options = book_resp.json().get('result', [])
                
                # Find an active Call option near the target strike
                # Prefer shorter duration (e.g., next week/month) for reactive Greeks
                best_opt = None
                for opt in options:
                    name = opt['instrument_name']
                    # Simple heuristic: Look for strike in name AND Call option ("-C")
                    if str(target_strike) in name and name.endswith('C'):
                        best_opt = opt
                        break # Just take the first one (usually nearest expiry)
                
                if best_opt:
                    name = best_opt['instrument_name']
                    
                    # 4. Get Ticker for this specific option (contains Greeks)
                    ticker_url = f"{self.base_url}/ticker"
                    ticker_resp = requests.get(ticker_url, params={"instrument_name": name}, timeout=5)
                    
                    if ticker_resp.status_code == 200:
                        ticker_data = ticker_resp.json().get('result', {})
                        greeks = ticker_data.get('greeks', {})
                        
                        if greeks:
                            # Safely get values, handling None
                            delta = greeks.get('delta') or 0.0
                            gamma = greeks.get('gamma') or 0.0
                            theta = greeks.get('theta') or 0.0
                            vega = greeks.get('vega') or 0.0
                            iv = ticker_data.get('mark_iv') or 0.0

                            with self.lock:
                                self.latest_data["delta_bs"] = float(delta)
                                self.latest_data["gamma_bs"] = float(gamma)
                                self.latest_data["theta_bs"] = float(theta)
                                self.latest_data["vega_bs"] = float(vega)
                                self.latest_data["implied_volatility"] = float(iv)
                            
                            print(f"✅ Deribit Greeks ({name}): IV={iv:.2f}, Delta={delta:.4f}, Vega={vega:.4f}")

        except Exception as e:
            print(f"⚠️ Deribit Greeks Error: {e}")

    def fetch_perpetual_stats(self):
        """
        Fetch BTC-PERPETUAL stats for backup data
        (Funding Rate & Open Interest)
        """
        try:
            url = f"{self.base_url}/ticker"
            params = {"instrument_name": "BTC-PERPETUAL"}
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json().get('result', {})
                
                with self.lock:
                    funding = data.get("current_funding", 0) or data.get("funding_8h", 0)
                    oi = data.get("open_interest", 0)
                    
                    if funding != 0:
                        self.latest_data["backup_funding_rate"] = float(funding)
                    if oi != 0:
                        self.latest_data["backup_open_interest"] = float(oi)

        except Exception as e:
            # print(f"❌ Deribit Backup Error: {e}")
            pass 

    def get_latest_data(self) -> Dict[str, Any]:
        """Fetch latest data (Perpetual + Greeks)"""
        start_time = time.time()
        success = False
        error_type = None
        error_message = None
        
        try:
            # 1. Fetch Perpetual Data (Price, OI, Funding)
            self.fetch_perpetual_stats()
            
            # 2. Fetch Option Greeks (ATM Proxy)
            # We call this every time in this loop (controlled by run() sleep)
            # or we can check timestamp. Since run() sleeps 10s, calling checks 10s is fine.
            self.fetch_atm_option_greeks()
            
            success = True
            
        except Exception as e:
            error_type = "ProcessingError"
            error_message = str(e)
            print(f"❌ Deribit Main Loop Error: {e}")
        
        with self.lock:
            return self.latest_data.copy()

    def get_backup_funding_rate(self) -> Optional[float]:
        with self.lock:
            return self.latest_data.get("backup_funding_rate")

    def get_backup_open_interest(self) -> Optional[float]:
        with self.lock:
            return self.latest_data.get("backup_open_interest")

    def stop(self):
        self.running = False
