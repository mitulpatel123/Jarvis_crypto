import requests
import time
import hmac
import hashlib
import json
import logging
from urllib.parse import urlencode
from src.config.settings import settings

logger = logging.getLogger(__name__)

class DeltaClient:
    BASE_URL = "https://api.india.delta.exchange"

    def __init__(self):
        self.api_key = settings.DELTA_API_KEY
        self.api_secret = settings.DELTA_API_SECRET
        self.session = requests.Session()

    def _generate_signature(self, method, path, payload):
        timestamp = str(int(time.time()))
        if payload:
            payload_str = json.dumps(payload) if method in ['POST', 'PUT'] else urlencode(payload)
        else:
            payload_str = ""
        
        signature_data = method + timestamp + path + payload_str
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature, timestamp

    def _request(self, method, endpoint, params=None, data=None, auth=False):
        url = f"{self.BASE_URL}{endpoint}"
        headers = {'Content-Type': 'application/json'}

        if auth:
            if not self.api_key or not self.api_secret:
                raise ValueError("API credentials not set")
            
            payload = data if method in ['POST', 'PUT'] else params
            signature, timestamp = self._generate_signature(method, endpoint, payload)
            headers.update({
                'api-key': self.api_key,
                'signature': signature,
                'timestamp': timestamp
            })

        try:
            response = self.session.request(method, url, params=params, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}")
            if 'response' in locals() and response is not None:
                logger.error(f"Response Status: {response.status_code}")
                logger.error(f"Response Body: {response.text}")
            raise

    def get_ticker(self, symbol):
        """Get current ticker info for a symbol."""
        return self._request('GET', '/v2/tickers', params={'symbol': symbol})

    def get_history(self, symbol, resolution, start=None, end=None, limit=1000):
        """
        Get historical OHLC data.
        resolution: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 1d
        """
        params = {
            'symbol': symbol,
            'resolution': resolution,
            'limit': limit
        }
        
        # Auto-calculate start/end if not provided
        if not end:
            end = int(time.time())
        if not start:
            # Estimate start based on resolution and limit to fetch enough data
            # Map resolution to seconds
            res_map = {
                '1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800,
                '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600, '1d': 86400
            }
            res_seconds = res_map.get(resolution, 60)
            start = end - (limit * res_seconds)

        params['start'] = start
        params['end'] = end
            
        return self._request('GET', '/v2/history/candles', params=params)

    def place_order(self, symbol, side, order_type, quantity, price=None, stop_price=None):
        """
        Place a new order.
        side: 'buy' or 'sell'
        order_type: 'limit', 'market', 'stop_limit', 'stop_market'
        """
        data = {
            'product_symbol': symbol,
            'size': int(quantity),
            'side': side,
            'order_type': order_type
        }
        if price:
            data['limit_price'] = str(price)
        if stop_price:
            data['stop_price'] = str(stop_price)
            
        return self._request('POST', '/v2/orders', data=data, auth=True)

    def get_balances(self):
        """Get wallet balances."""
        return self._request('GET', '/v2/wallet/balances', auth=True)

    def get_products(self):
        """
        Fetch all available products from Delta Exchange.
        """
        try:
            return self._request('GET', '/v2/products')
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return {'result': []}

delta_client = DeltaClient()
