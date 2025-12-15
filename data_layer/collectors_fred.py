"""
FRED (Federal Reserve Economic Data) API Collector
Provides: DXY, 10Y Treasury Yields, M2 Money Supply
Refactored to use DIRECT HTTP requests (Reliable) instead of fredapi
"""

import threading
import time
import requests
import os
from datetime import datetime

class FREDCollector(threading.Thread):
    def __init__(self, key_manager):
        super().__init__()
        self.daemon = True
        self.running = False
        self.lock = threading.Lock()
        self.key_manager = key_manager
        
        # FRED series IDs
        self.series_ids = {
            "dxy": "DTWEXBGS",  # Trade Weighted U.S. Dollar Index
            "treasury_10y": "DGS10",  # 10-Year Treasury Constant Maturity Rate
            "m2_money": "WM2NS"  # M2 Money Stock (Billions)
        }
        
        self.latest_data = {
            "dxy_fred": 0.0,
            "treasury_10y": 0.0,
            "m2_money_supply": 0.0
        }
        print("✅ FREDCollector (Direct HTTP) initialized")
    
    def fetch_series_data(self, series_id, data_key):
        """Fetch latest data point directly from FRED API"""
        try:
            # Get next key (rotation)
            if not self.key_manager.increment("fred"):
                return False
                
            key_info = self.key_manager.get_key("fred")
            if not key_info:
                print("❌ FRED: No API key available")
                return False
            
            api_key = key_info.get("api_key") or key_info.get("token")
            
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                "series_id": series_id,
                "api_key": api_key,
                "file_type": "json",
                "limit": 1,
                "sort_order": "desc"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                observations = data.get('observations', [])
                
                if observations:
                    latest = observations[0]
                    value_str = latest.get('value', '.')
                    
                    if value_str == '.':
                        print(f"⚠️  FRED {data_key}: Data is present but value is missing ('.')")
                        return False
                        
                    value = float(value_str)
                    
                    # M2 is in billions, convert to trillions
                    if data_key == "m2_money_supply":
                        value = value / 1000
                    
                    with self.lock:
                        self.latest_data[data_key] = value
                    return True
                else:
                    print(f"⚠️  FRED {data_key}: No observations returned")
                    return False
            elif response.status_code == 429:
                 print(f"⚠️  FRED Rate Limit (429) - Rotating key next time")
                 return False
            else:
                 print(f"❌ FRED HTTP {response.status_code}: {response.text}")
                 return False
                        
        except Exception as e:
            print(f"❌ FRED {data_key} Error: {e}")
            return False
    
    def run(self):
        """Main collection loop - runs every 1 hour"""
        self.running = True
        
        while self.running:
            try:
                success_count = 0
                if self.fetch_series_data(self.series_ids["dxy"], "dxy_fred"): success_count += 1
                time.sleep(2)
                
                if self.fetch_series_data(self.series_ids["treasury_10y"], "treasury_10y"): success_count += 1
                time.sleep(2)
                
                if self.fetch_series_data(self.series_ids["m2_money"], "m2_money_supply"): success_count += 1
                
                # Print status
                dxy = self.latest_data['dxy_fred']
                treasury = self.latest_data['treasury_10y']
                m2 = self.latest_data['m2_money_supply']
                
                if success_count > 0:
                    print(f"✅ FRED Updated: DXY={dxy:.2f}, 10Y={treasury:.3f}%, M2=${m2:.2f}T")
                
                # Sleep for 1 hour
                time.sleep(3600)
                
            except Exception as e:
                print(f"❌ FRED thread error: {e}")
                time.sleep(300)
    
    def get_snapshot(self):
        with self.lock:
            return self.latest_data.copy()
    
    def stop(self):
        self.running = False
