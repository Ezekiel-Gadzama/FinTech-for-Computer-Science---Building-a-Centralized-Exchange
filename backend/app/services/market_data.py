import requests
from datetime import datetime, timedelta
from typing import Dict, List
import json


class MarketDataService:
    """Service for fetching and caching market data"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.cache_duration = 30  # seconds

    def get_prices(self) -> Dict:
        """Get current prices for all supported pairs"""
        cache_key = 'market:prices'

        # Try cache first
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except:
                pass

        # Fetch from API
        prices = self._fetch_prices_from_api()

        # Cache result
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    self.cache_duration,
                    json.dumps(prices)
                )
            except:
                pass

        return prices

    def _fetch_prices_from_api(self) -> Dict:
        """Fetch prices from CoinGecko API"""
        try:
            symbols = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana']
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ','.join(symbols),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                return {
                    'BTC/USDT': {
                        'price': data.get('bitcoin', {}).get('usd', 0),
                        'change_24h': data.get('bitcoin', {}).get('usd_24h_change', 0),
                        'volume_24h': data.get('bitcoin', {}).get('usd_24h_vol', 0)
                    },
                    'ETH/USDT': {
                        'price': data.get('ethereum', {}).get('usd', 0),
                        'change_24h': data.get('ethereum', {}).get('usd_24h_change', 0),
                        'volume_24h': data.get('ethereum', {}).get('usd_24h_vol', 0)
                    },
                    'BNB/USDT': {
                        'price': data.get('binancecoin', {}).get('usd', 0),
                        'change_24h': data.get('binancecoin', {}).get('usd_24h_change', 0),
                        'volume_24h': data.get('binancecoin', {}).get('usd_24h_vol', 0)
                    },
                    'ADA/USDT': {
                        'price': data.get('cardano', {}).get('usd', 0),
                        'change_24h': data.get('cardano', {}).get('usd_24h_change', 0),
                        'volume_24h': data.get('cardano', {}).get('usd_24h_vol', 0)
                    },
                    'SOL/USDT': {
                        'price': data.get('solana', {}).get('usd', 0),
                        'change_24h': data.get('solana', {}).get('usd_24h_change', 0),
                        'volume_24h': data.get('solana', {}).get('usd_24h_vol', 0)
                    }
                }
        except Exception as e:
            print(f"Error fetching prices: {e}")

        # Fallback data
        return {
            'BTC/USDT': {'price': 45000, 'change_24h': 2.5, 'volume_24h': 1000000000},
            'ETH/USDT': {'price': 2500, 'change_24h': 1.8, 'volume_24h': 500000000},
            'BNB/USDT': {'price': 300, 'change_24h': -0.5, 'volume_24h': 100000000},
            'ADA/USDT': {'price': 0.5, 'change_24h': 3.2, 'volume_24h': 50000000},
            'SOL/USDT': {'price': 100, 'change_24h': 5.1, 'volume_24h': 200000000}
        }


market_data_service = MarketDataService()