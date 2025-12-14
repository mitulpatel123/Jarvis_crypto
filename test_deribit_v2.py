import requests
import json
import time

print("🔍 Testing Deribit Endpoints (v2.2 Debug)")
print("-----------------------------------------")

def test_endpoint(name, endpoint):
    url = f"https://www.deribit.com/api/v2/{endpoint}"
    params = {"instrument_name": "BTC-PERPETUAL"}
    print(f"\n📡 Testing '{name}': {url}...")
    
    try:
        response = requests.get(url, params=params, timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result')
            
            # Handle list vs dict result
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            print(f"   ✅ SUCCESS. Keys found: {list(result.keys())[:5]}...")
            
            oi = result.get('open_interest')
            funding = result.get('current_funding') or result.get('funding_8h')
            
            print(f"   📊 Data: Funding={funding}, OI={oi}")
            return True
        else:
            print(f"   ❌ FAILED: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        return False

# Test 1: ticker
test_endpoint("Ticker", "public/ticker")

# Test 2: get_book_summary_by_instrument
test_endpoint("Book Summary", "public/get_book_summary_by_instrument")
