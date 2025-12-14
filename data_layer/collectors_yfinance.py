"""
Yahoo Finance Collector (Free, No API Key Required)
Provides SPX and DXY correlations with BTC
"""

import threading
import time
import logging
from typing import Dict, Any

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    # Suppress yfinance warnings
    logging.getLogger('yfinance').setLevel(logging.CRITICAL)
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not installed. Run: pip install yfinance")


class YahooFinanceCollector(threading.Thread):
    """
    Yahoo Finance Collector for Market Correlations
    Calculates correlation between BTC and SPX/DXY
    """
    
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = False
        self.lock = threading.Lock()
        self.latest_data = {
            "correlation_spx": 0.0,
            "correlation_dxy": 0.0
        }
        
        if YFINANCE_AVAILABLE:
            print("✅ YahooFinanceCollector initialized")
        else:
            print("❌ YahooFinanceCollector: yfinance library not available")
    
    def run(self):
        """Background thread loop - updates every 5 minutes"""
        if not YFINANCE_AVAILABLE:
            return
            
        self.running = True
        
        # Initial fetch
        self.fetch_correlations()
        
        while self.running:
            time.sleep(300)  # Update every 5 minutes
            try:
                self.fetch_correlations()
            except Exception as e:
                print(f"❌ YahooFinance: Unexpected error - {e}")
    
    def fetch_correlations(self):
        """Fetch market data and calculate correlations"""
        if not YFINANCE_AVAILABLE:
            return
            
        try:
            # Symbols: ^GSPC (S&P 500), DX-Y.NYB (US Dollar Index), BTC-USD
            tickers = ['BTC-USD', '^GSPC', 'DX-Y.NYB']
            data_frames = []

            for ticker in tickers:
                try:
                    data = yf.Ticker(ticker)
                    hist = data.history(period="30d", interval="1d")  # Use daily data for better correlation
                    if not hist.empty:
                        # Create a DataFrame with just the Close price and datetime index
                        df = hist[['Close']].rename(columns={'Close': ticker})
                        data_frames.append(df)
                except Exception as e:
                    print(f"⚠️  YahooFinance: Error fetching {ticker} - {e}")

            # Combine data using outer join
            if data_frames:
                combined_df = data_frames[0]
                for df in data_frames[1:]:
                    combined_df = combined_df.join(df, how='outer')
                
                # Forward fill and backward fill to handle timezone differences
                combined_df = combined_df.fillna(method='ffill').fillna(method='bfill')
                
                # Drop any remaining NaN values
                combined_df = combined_df.dropna()
                
                if len(combined_df) >= 10:
                    # Calculate correlation matrix
                    corr_matrix = combined_df.corr()
                    
                    # Extract correlations with BTC-USD
                    if 'BTC-USD' in corr_matrix.columns:
                        spx_corr = corr_matrix.loc['BTC-USD', '^GSPC'] if '^GSPC' in corr_matrix.columns else 0.0
                        dxy_corr = corr_matrix.loc['BTC-USD', 'DX-Y.NYB'] if 'DX-Y.NYB' in corr_matrix.columns else 0.0
                        
                        with self.lock:
                            self.latest_data["correlation_spx"] = float(spx_corr) if pd.notna(spx_corr) else 0.0
                            self.latest_data["correlation_dxy"] = float(dxy_corr) if pd.notna(dxy_corr) else 0.0
                        
                        print(f"✅ YahooFinance: SPX Corr={spx_corr:.3f}, DXY Corr={dxy_corr:.3f}")
                    else:
                        print("⚠️  YahooFinance: BTC-USD not in correlation matrix")
                else:
                    print("⚠️  YahooFinance: Insufficient data points for correlation")
            else:
                print("⚠️  YahooFinance: No data downloaded")
                
        except Exception as e:
            print(f"❌ YahooFinance: Error fetching data - {e}")
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Get current correlation snapshot"""
        with self.lock:
            return self.latest_data.copy()
    
    def stop(self):
        """Stop the collector"""
        self.running = False
        if YFINANCE_AVAILABLE:
            print("✅ YahooFinanceCollector stopped")