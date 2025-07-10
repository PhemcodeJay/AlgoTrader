import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional

class DataProvider:
    BASE_URL = "https://api.binance.com/api/v3"

    def __init__(self):
        self.session = requests.Session()

    def get_popular_symbols(self, limit: int = 30) -> List[str]:
        """
        Fetch top trading pairs by volume (USDT only).
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/ticker/24hr")
            data = response.json()
            usdt_pairs = [item for item in data if item["symbol"].endswith("USDT")]
            sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x["quoteVolume"]), reverse=True)
            return [pair["symbol"] for pair in sorted_pairs[:limit]]
        except Exception as e:
            print(f"[DataProvider] Error fetching popular symbols: {e}")
            return []

    def get_market_overview(self, limit: int = 10) -> List[Dict]:
        """
        Fetch 24h summary for top USDT symbols.
        """
        try:
            symbols = self.get_popular_symbols(limit)
            response = self.session.get(f"{self.BASE_URL}/ticker/24hr")
            tickers = response.json()
            symbol_map = {item["symbol"]: item for item in tickers}

            overview = []
            for sym in symbols:
                item = symbol_map.get(sym)
                if not item:
                    continue

                overview.append({
                    "symbol": sym,
                    "price": float(item["lastPrice"]),
                    "price_change_pct": float(item["priceChangePercent"]),
                    "volume": float(item["quoteVolume"])
                })

            return overview
        except Exception as e:
            print(f"[DataProvider] Market overview error: {e}")
            return []

    def get_chart_data(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict]]:
        """
        Fetch OHLCV (candlestick) data for plotting technical indicators.
        Output format matches requirements of DashboardComponents.create_technical_chart().
        """
        try:
            url = f"{self.BASE_URL}/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }

            response = self.session.get(url, params=params)
            raw_data = response.json()

            formatted = []
            for entry in raw_data:
                formatted.append({
                    "timestamp": datetime.fromtimestamp(entry[0] / 1000, tz=timezone.utc),
                    "open": float(entry[1]),
                    "high": float(entry[2]),
                    "low": float(entry[3]),
                    "close": float(entry[4]),
                    "volume": float(entry[5])
                })

            return formatted
        except Exception as e:
            print(f"[DataProvider] Failed to get chart data for {symbol}: {e}")
            return None
