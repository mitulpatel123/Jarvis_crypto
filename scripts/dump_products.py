from src.data.delta_client import delta_client
import json

def main():
    try:
        response = delta_client._request('GET', '/v2/products')
        products = response['result']
        
        with open('products.json', 'w') as f:
            json.dump(products, f, indent=2)
            
        print(f"Dumped {len(products)} products to products.json")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
