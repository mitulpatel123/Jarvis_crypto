import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from infrastructure.timescale_db import TimescaleDB

def verify_fresh_data():
    print("🔍 Fetching recent data snapshot from Database...")
    
    try:
        db = TimescaleDB(host='localhost') # Assuming running on VPS localhost
        conn = db.get_conn()
        
        # Fetch last 100 rows
        query = "SELECT * FROM feature_store ORDER BY timestamp DESC LIMIT 100"
        df = pd.read_sql(query, conn)
        
        if df.empty:
            print("❌ No data found!")
            return

        print(f"✅ Downloaded {len(df)} rows.")
        timestamp_range = f"{df['timestamp'].min()} to {df['timestamp'].max()}"
        print(f"📅 Range: {timestamp_range}")
        
        # Save for manual inspection
        df.to_csv("fresh_data_sample.csv", index=False)
        print("💾 Saved snapshot to 'fresh_data_sample.csv'")

        # --- QUALITY CHECK ---
        print("\n🔎 Verifying Critical Fixed Columns:")
        
        checks = {
            "long_short_ratio": "Binance L/S Ratio",
            "delta_bs": "Option Delta (Greeks)",
            "vega_bs": "Option Vega (Greeks)",
            "treasury_10y": "FRED 10Y Treasury",
            "news_sentiment": "CryptoPanic Sentiment"
        }
        
        all_passed = True
        
        for col, name in checks.items():
            if col not in df.columns:
                print(f"   ❓ {name}: Column Missing!")
                all_passed = False
                continue
                
            # Check for non-zero values
            non_zero = df[df[col] != 0]
            val = df[col].iloc[0] # Most recent value
            
            if len(non_zero) > 0:
                print(f"   ✅ {name}: OK (Latest: {val})")
            else:
                print(f"   ❌ {name}: ALL ZEROS (Still Dead?)")
                all_passed = False

        if all_passed:
            print("\n🎉 SUCCESS: All fixed columns are receiving data!")
        else:
            print("\n⚠️  WARNING: Some columns are still effectively dead.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'db' in locals():
            db.put_conn(conn)

if __name__ == "__main__":
    verify_fresh_data()
