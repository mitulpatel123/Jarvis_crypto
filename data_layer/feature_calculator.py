"""
Feature Calculator for Crypto Data Factory
Responsible for:
1. Calculating derived features (Volatility, Time)
2. Normalizing and merging data from multiple collectors
3. Ensuring all 62+ database columns are populated
"""

import time
import numpy as np
from datetime import datetime
from typing import Dict, Any, List

class FeatureCalculator:
    """
    Central processing unit for raw collector data.
    Ensures data consistency and completeness before DB insertion.
    """
    
    def __init__(self):
        # Settings for calculations
        self.volatility_window = 60  # 1 hour window for HV calculation (assuming 1m updates)
        self.price_history: List[float] = []
        self.last_cleanup = time.time()
        
        print("✅ FeatureCalculator initialized")

    def calculate_features(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: Transform raw collector data into final DB row.
        """
        derived = {}
        
        # 1. Time Features (Critical for ML)
        now = datetime.utcnow()
        derived['time_hour'] = now.hour
        derived['time_day'] = now.weekday()  # 0=Monday, 6=Sunday
        derived['is_weekend'] = now.weekday() >= 5
        
        # 2. Historical Volatility (HV)
        # We need a stream of close prices to calculate this
        current_price = raw_data.get('close')
        if current_price and current_price > 0:
            self._update_price_history(current_price)
            derived['volatility_hv'] = self._calculate_hv()
        else:
            derived['volatility_hv'] = 0.0
            
        # 3. Greeks Normalization & Fallbacks
        # If API gives specific Greek, use it. If not, try fallback or default to 0.
        
        # Delta (prefer Deribit 'delta_bs', fallback to 'delta', then 'delta_exposure')
        derived['delta_bs'] = raw_data.get('delta_bs', raw_data.get('delta', raw_data.get('delta_exposure', 0.0)))
        
        # Gamma
        derived['gamma_bs'] = raw_data.get('gamma_bs', raw_data.get('gamma', 0.0))
        
        # Theta
        derived['theta_bs'] = raw_data.get('theta_bs', raw_data.get('theta', 0.0))
        
        # Vega
        derived['vega_bs'] = raw_data.get('vega_bs', raw_data.get('vega', 0.0))
        
        # 4. Derivative Metrics Normalization
        
        # Put/Call Ratio: Merge sources if multiple exist
        # Priority: Deribit PCR -> Delta PCR Vol -> Delta PCR OI
        pcr = raw_data.get('put_call_ratio') # From Deribit if available directly
        if pcr is None:
             pcr = raw_data.get('put_call_ratio_vol')
        if pcr is None:
             pcr = raw_data.get('put_call_ratio_oi')
        
        derived['put_call_ratio'] = float(pcr) if pcr is not None else 0.0
        
        # 5. Fill Missing Core Fields (Data Safety)
        # Ensure no KeyErrors for the 60-column schema
        defaults = {
            'vwap': raw_data.get('close', 0), # Fallback to close if VWAP missing
            'trade_count': 0,
            'volume': 0.0,
            'volume_buy': 0.0,
            'volume_sell': 0.0,
            'bid_ask_spread': 0.0,
            'ob_imbalance_5': 0.0,
            'liquidation_long_1h': 0.0,
            'liquidation_short_1h': 0.0,
            'liquidation_total_1h': 0.0,
            'funding_rate': 0.0,
            'open_interest': 0.0,
            'whale_inflow': 0.0,
            'whale_outflow': 0.0,
            'news_sentiment': 0.0,
            'social_hype_index': 0.0,
            'fear_greed_index': 50.0, # Neutral default
            'correlation_spx': 0.0,
            'correlation_dxy': 0.0,
            'dxy_fred': 0.0,
            'treasury_10y': 0.0,
            'm2_money_supply': 0.0
        }
        
        for key, default_val in defaults.items():
            if key not in raw_data or raw_data[key] is None:
                derived[key] = default_val
            else:
                # Ensure correct type (float)
                try:
                    derived[key] = float(raw_data[key])
                except (ValueError, TypeError):
                    derived[key] = default_val

        return derived

    def _update_price_history(self, price: float):
        """Update internal price history for volatility calc"""
        self.price_history.append(price)
        
        # Keep fixed window size
        if len(self.price_history) > self.volatility_window:
            self.price_history.pop(0)

    def _calculate_hv(self) -> float:
        """
        Calculate annualized Historical Volatility
        """
        if len(self.price_history) < 2:
            return 0.0
            
        try:
            prices = np.array(self.price_history)
            returns = np.diff(np.log(prices))
            std_dev = np.std(returns)
            
            # Annualize (assuming 1-minute data points * 525600 min/year)
            # Typically crypto trades 24/7 => 365 * 24 * 60 = 525600
            annualized_vol = std_dev * np.sqrt(525600) 
            return float(annualized_vol)
        except Exception:
            return 0.0
