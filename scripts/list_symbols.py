import json

def main():
    try:
        with open('products.json', 'r') as f:
            products = json.load(f)
        
        print(f"Loaded {len(products)} products.")
        
        print("\nSearching for BTC futures...")
        for p in products:
            symbol = p.get('symbol', '')
            contract_type = p.get('contract_type', '')
            
            if 'BTC' in symbol and ('future' in contract_type or 'spot' in contract_type):
                print(f"Symbol: {symbol}, Type: {contract_type}, ID: {p.get('id')}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
