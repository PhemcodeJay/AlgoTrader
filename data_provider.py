import requests
import json
from datetime import datetime, timedelta

class DataProvider:
    def __init__(self):
        self.base_url = "https://fapi.binance.com/fapi/v1"
    
    def get_popular_symbols(self):
        """Get list of popular trading symbols"""
        try:
            url = f"{self.base_url}/exchangeInfo"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            symbols = [s['symbol'] for s in data['symbols'] 
                      if s['contractType'] == 'PERPETUAL' and 'USDT' in s['symbol']]
            
            # Return top 50 most popular symbols
            popular_symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
                'DOGEUSDT', 'SOLUSDT', 'TRXUSDT', 'DOTUSDT', 'MATICUSDT',
                'LTCUSDT', 'AVAXUSDT', 'LINKUSDT', 'ATOMUSDT', 'UNIUSDT',
                'XLMUSDT', 'ALGOUSDT', 'VETUSDT', 'FILUSDT', 'ICPUSDT'
            ]
            
            # Filter to only include symbols that exist
            return [s for s in popular_symbols if s in symbols][:20]
            
        except Exception as e:
            print(f"Error fetching symbols: {e}")
            # Return fallback symbols
            return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT']
    
    def get_chart_data(self, symbol, timeframe='1h', limit=100):
        """Get OHLCV data for charting"""
        try:
            url = f"{self.base_url}/klines"
            params = {
                'symbol': symbol,
                'interval': timeframe,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            # Return [high, low, close, volume, open] format
            return [[float(x[2]), float(x[3]), float(x[4]), float(x[5]), float(x[1])] for x in data]
            
        except Exception as e:
            print(f"Error fetching chart data for {symbol}: {e}")
            return []
    
    def get_market_overview(self):
        """Get market overview for top symbols"""
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT', 'DOTUSDT']
        market_data = {}
        
        try:
            # Get 24hr ticker data
            url = f"{self.base_url}/ticker/24hr"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for ticker in data:
                symbol = ticker['symbol']
                if symbol in symbols:
                    market_data[symbol] = {
                        'price': float(ticker['lastPrice']),
                        'price_change_pct': float(ticker['priceChangePercent']),
                        'volume': float(ticker['volume']),
                        'high_24h': float(ticker['highPrice']),
                        'low_24h': float(ticker['lowPrice'])
                    }
            
            return market_data
            
        except Exception as e:
            print(f"Error fetching market overview: {e}")
            # Return mock data for demonstration
            return {
                'BTCUSDT': {'price': 45000, 'price_change_pct': 2.5, 'volume': 1000000, 'high_24h': 46000, 'low_24h': 44000},
                'ETHUSDT': {'price': 3200, 'price_change_pct': -1.2, 'volume': 800000, 'high_24h': 3250, 'low_24h': 3150},
                'BNBUSDT': {'price': 420, 'price_change_pct': 0.8, 'volume': 300000, 'high_24h': 425, 'low_24h': 415},
                'XRPUSDT': {'price': 0.65, 'price_change_pct': 3.2, 'volume': 200000, 'high_24h': 0.67, 'low_24h': 0.63}
            }
    
    def get_current_price(self, symbol):
        """Get current price for a symbol"""
        try:
            url = f"{self.base_url}/ticker/price"
            params = {'symbol': symbol}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            return float(data['price'])
            
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    def get_market_summary(self):
        """Get overall market summary statistics"""
        try:
            url = f"{self.base_url}/ticker/24hr"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Filter USDT pairs
            usdt_pairs = [ticker for ticker in data if ticker['symbol'].endswith('USDT')]
            
            if not usdt_pairs:
                return None
            
            # Calculate market statistics
            total_volume = sum(float(ticker['quoteVolume']) for ticker in usdt_pairs)
            avg_change = sum(float(ticker['priceChangePercent']) for ticker in usdt_pairs) / len(usdt_pairs)
            
            gainers = len([t for t in usdt_pairs if float(t['priceChangePercent']) > 0])
            losers = len([t for t in usdt_pairs if float(t['priceChangePercent']) < 0])
            
            return {
                'total_volume': total_volume,
                'avg_change': avg_change,
                'gainers': gainers,
                'losers': losers,
                'total_pairs': len(usdt_pairs)
            }
            
        except Exception as e:
            print(f"Error fetching market summary: {e}")
            return None
