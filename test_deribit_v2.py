import requests
import json
import time

print("🔍 Testing Deribit BTC-PERPETUAL Data Fetch (v2.1 Debug)")
print("-------------------------------------------------------")

url = "https://www.deribit.com/api/v2/public/get_ticker"
params = {"instrument_name": "BTC-PERPETUAL"}

try:
    print(f"📡 Sending request to {url}...")
    start = time.time()
    response = requests.get(url, params=params, timeout=10)
    latency = (time.time() - start) * 1000
    
    print(f"✅ Status Code: {response.status_code} ({latency:.0f}ms)")
    
    if response.status_code == 200:
        data = response.json()
        result = data.get('result', {})
        
        # 1. Print Raw Keys to see what exists
        print("\n🔑 Available Keys in Response:")
        print(list(result.keys()))
        
        # 2. Extract Specific Values
        funding_8h = result.get('funding_8h')
        current_funding = result.get('current_funding')
        open_interest = result.get('open_interest')
        mark_price = result.get('mark_price')
        
        print("\n📊 Extracted Data:")
        print(f"   - Mark Price:      {mark_price}")
        print(f"   - Open Interest:   {open_interest}")
        print(f"   - Funding (8h):    {funding_8h}")
        print(f"   - Funding (Curr):  {current_funding}")
        
        # 3. Check for 0
        if open_interest == 0 or open_interest is None:
            print("\n❌ ISSUE: Open Interest is ZERO or None!")
        else:
            print("\n✅ SUCCESS: Open Interest is valid.")
            
    else:
        print(f"❌ Error: HTTP {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"\n❌ CRITICAL ERROR: {e}")
