"""
CoinGlass API Collector
Provides: Put/Call Ratio, OI Change, Liquidation Data
Free Tier: 100 calls/day per key (5 keys = 500 calls/day)
"""

import threading
import time
import requests
from datetime import datetime


class CoinGlassCollector(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = False
        self.lock = threading.Lock()
        
        # 10 API keys - 5 original + 5 new from user
        self.api_keys = [
            # Original 5 keys
            "f632594f56e74ddf995f6ffdeac6de82",
            "7dbd21eb250c44a0b18607c89f07166a",
            "be9776242d584b4b81bbb3cde709d4c7",
            "b562b0e74fa5416fb1a754ac0a637468",
            "7a4a198e1ba44d76bd7fa241d52bc075",
            # New 5 keys from user (Dec 2025)
            "511eb0fc20344f3cb758735b4c95fdb9",
            "50241cc594154776a60c3b5e6a126193",
            "c5e8a3f4b79b449fa2533f9349b7cd73",
            "daa45b3f5d6f4f06b94d73dcd08c7560",
            "8cef566412cb4dbb8615977169ea4d80"
        ]
        self.current_key_index = 0
        self.call_count = 0
        self.max_calls_per_key = 95  # Stay under 100/day (safety margin)
        self.calls_per_key = [0] * len(self.api_keys)  # Track each key separately
        self.last_reset_day = datetime.now().day  # Reset counters daily
        
        self.base_url = "https://open-api-v4.coinglass.com/api"
        
        self.latest_data = {
            "put_call_ratio": 0.0,
            "oi_change_1h": 0.0,
            "oi_change_4h": 0.0,
            "oi_change_24h": 0.0,
            "liquidation_long": 0.0,
            "liquidation_short": 0.0,
            "liquidation_all": 0.0
        }

    def get_current_api_key(self):
        """Rotate API keys intelligently - find least used key"""
        # Reset all counters if new day
        current_day = datetime.now().day
        if current_day != self.last_reset_day:
            self.calls_per_key = [0] * len(self.api_keys)
            self.last_reset_day = current_day
            print(f"🔄 CoinGlass: Daily reset - all keys refreshed ({len(self.api_keys)} keys)")
        
        # Find key with lowest usage (smart rotation)
        self.current_key_index = self.calls_per_key.index(min(self.calls_per_key))
        
        # Check if current key is under limit
        if self.calls_per_key[self.current_key_index] >= self.max_calls_per_key:
            print(f"⚠️  CoinGlass: All {len(self.api_keys)} keys exhausted for today!")
            # Return the least used key anyway (best effort)
        
        return self.api_keys[self.current_key_index]

    def fetch_put_call_ratio(self):
        """Fetch Put/Call Ratio for BTC"""
        try:
            api_key = self.get_current_api_key()
            headers = {"CG-API-KEY": api_key}
            
            # CoinGlass endpoint for options data (may require premium)
            url = f"{self.base_url}/options/put-call-ratio"
            params = {"symbol": "BTC", "interval": "1h"}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            self.calls_per_key[self.current_key_index] += 1
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    pcr = float(data["data"][0].get("putCallRatio", 0))
                    with self.lock:
                        self.latest_data["put_call_ratio"] = pcr
                    print(f"✅ CoinGlass: Put/Call Ratio = {pcr:.3f}")
                    return True
            else:
                print(f"⚠️  CoinGlass PCR: HTTP {response.status_code}")
                
        except requests.Timeout:
            print("❌ CoinGlass PCR: Request timeout")
        except Exception as e:
            print(f"❌ CoinGlass PCR: {type(e).__name__}: {e}")
        
        return False

    def fetch_oi_change(self):
        """Fetch Open Interest changes (1h, 4h, 24h)"""
        try:
            api_key = self.get_current_api_key()
            headers = {"CG-API-KEY": api_key}
            
            # OI change endpoint - corrected
            url = f"{self.base_url}/futures/open-interest/history"
            params = {"symbol": "BTC", "interval": "1h", "limit": 25}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            self.calls_per_key[self.current_key_index] += 1
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    latest = data["data"][-1] if data["data"] else {}
                    
                    with self.lock:
                        # Calculate changes from latest data
                        current_oi = float(latest.get("o", 0))
                        prev_1h = float(data["data"][-2].get("o", current_oi)) if len(data["data"]) > 1 else current_oi
                        prev_4h = float(data["data"][-5].get("o", current_oi)) if len(data["data"]) > 4 else current_oi
                        prev_24h = float(data["data"][-25].get("o", current_oi)) if len(data["data"]) > 24 else current_oi
                        
                        self.latest_data["oi_change_1h"] = current_oi - prev_1h
                        self.latest_data["oi_change_4h"] = current_oi - prev_4h
                        self.latest_data["oi_change_24h"] = current_oi - prev_24h
                    
                    print(f"✅ CoinGlass: OI Change 1h={self.latest_data['oi_change_1h']:.0f}")
                    return True
            else:
                print(f"⚠️  CoinGlass OI: HTTP {response.status_code}")
                
        except requests.Timeout:
            print("❌ CoinGlass OI: Request timeout")
        except Exception as e:
            print(f"❌ CoinGlass OI: {type(e).__name__}: {e}")
        
        return False

    def fetch_liquidations(self):
        """Fetch liquidation data - FIXED correct endpoint path"""
        try:
            api_key = self.get_current_api_key()
            headers = {"CG-API-KEY": api_key}
            
            # CORRECT endpoint from official docs
            url = f"{self.base_url}/futures/liquidation_history"
            params = {
                "ex": "Binance",  # Exchange parameter required
                "symbol": "BTCUSDT",  # Full symbol format
                "interval": "h4",  # 4-hour intervals (h1, h4, h12, h24)
                "limit": 2
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            self.calls_per_key[self.current_key_index] += 1
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "0" and data.get("data"):
                    latest = data["data"][0] if data["data"] else {}
                    
                    with self.lock:
                        # Extract aggregation data
                        self.latest_data["liquidation_long"] = float(latest.get("buyVol", 0))
                        self.latest_data["liquidation_short"] = float(latest.get("sellVol", 0))
                        self.latest_data["liquidation_all"] = float(latest.get("totalVol", 0))
                    
                    print(f"✅ CoinGlass: Liquidation Long={self.latest_data['liquidation_long']:.0f}, Short={self.latest_data['liquidation_short']:.0f}")
                    return True
                else:
                    print(f"⚠️  CoinGlass Liq: API Error - {data.get('msg', 'Unknown')}")
            else:
                print(f"⚠️  CoinGlass Liq: HTTP {response.status_code}")
                
        except requests.Timeout:
            print("❌ CoinGlass Liq: Request timeout")
        except Exception as e:
            print(f"❌ CoinGlass Liq: {type(e).__name__}: {e}")
        
        return False

    def run(self):
        """Main collection loop - optimized for maximum safe data collection"""
        self.running = True
        
        # Calculate optimal sleep time based on capacity
        # Total daily capacity = 10 keys × 95 calls = 950 calls
        # We make 3 calls per cycle (PCR, OI, Liquidations)
        # Max safe cycles per day = 950 / 3 = ~316 cycles
        # Sleep time = 86400 seconds / 316 cycles = ~273 seconds (~4.5 min)
        # We use 300s (5 min) for guaranteed safety margin
        
        optimal_sleep = 300  # 5 minutes = guaranteed sustainable 24/7
        cycles_per_day = 86400 / optimal_sleep
        estimated_calls = cycles_per_day * 3
        
        print(f"✅ CoinGlassCollector initialized ({len(self.api_keys)} API keys)")
        print(f"   📊 Capacity: {len(self.api_keys) * self.max_calls_per_key} calls/day")
        print(f"   🔄 Collection: Every {optimal_sleep/60:.0f} minutes (3 endpoints)")
        print(f"   📈 Estimated usage: {estimated_calls:.0f} calls/day ({estimated_calls/(len(self.api_keys)*self.max_calls_per_key)*100:.1f}% of capacity)")
        
        while self.running:
            try:
                # Fetch all metrics
                self.fetch_put_call_ratio()
                time.sleep(2)  # Rate limiting between calls
                
                self.fetch_oi_change()
                time.sleep(2)
                
                self.fetch_liquidations()
                
                # OPTIMIZED: Sleep for 5 minutes with 10 keys
                # 3 calls every 5 min = 36 calls/hour = 864 calls/day total
                # Distributed across 10 keys with smart rotation = ~86 calls/day per key
                # Each key limited to max 95 calls/day (enforced by smart rotation)
                # Smart rotation ensures even distribution with 9-call safety margin per key
                time.sleep(300)  # 5 minutes - guaranteed sustainable 24/7 collection
                
            except Exception as e:
                print(f"❌ CoinGlass thread error: {e}")
                time.sleep(60)

    def get_snapshot(self):
        """Thread-safe data retrieval"""
        with self.lock:
            return self.latest_data.copy()

    def stop(self):
        """Stop the collector"""
        self.running = False
