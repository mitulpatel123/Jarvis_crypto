import json

def main():
    try:
        with open('products.json', 'r') as f:
            products = json.load(f)
        
        for p in products:
            if p['symbol'] == 'BTCUSD':
                print(json.dumps(p, indent=2))
                break
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
