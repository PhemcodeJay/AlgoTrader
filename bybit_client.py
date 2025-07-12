from pybit.unified_trading import HTTP
import os


class BybitClient:
    def __init__(self):
        self.use_real = os.getenv("USE_REAL_TRADING", "true").lower() == "true"
        self.session = HTTP(
            api_key=os.getenv("BYBIT_API_KEY"),
            api_secret=os.getenv("BYBIT_API_SECRET"),
            testnet=not self.use_real
        )

        mode = "LIVE TRADING MODE" if self.use_real else "TESTNET MODE"
        print(f"[BybitClient] Initialized in {mode}")

    def place_order(self, symbol, side, qty, entry_price=None, sl=None, tp=None):
        try:
            order = self.session.place_order(
                category="linear",  # Futures (USDT perpetual)
                symbol=symbol,
                side=side,
                order_type="Market",
                qty=qty,
                take_profit=tp,
                stop_loss=sl,
                reduce_only=False,
                time_in_force="GTC"
            )
            print(f"[BybitClient] Order placed: {order}")
            return order
        except Exception as e:
            print(f"[BybitClient] Order error: {e}")
            return None

    def cancel_order(self, symbol, order_id):
        try:
            result = self.session.cancel_order(
                category="linear",
                symbol=symbol,
                order_id=order_id
            )
            print(f"[BybitClient] Order cancelled: {result}")
            return result
        except Exception as e:
            print(f"[BybitClient] Cancel error: {e}")
            return None

    def get_balance(self, coin="USDT"):
        try:
            response = self.session.get_wallet_balance(accountType="UNIFIED")
            if "result" in response:
                balance_info = response["result"]["list"][0]["coin"]
                coin_balance = next((item for item in balance_info if item["coin"] == coin), None)
                print(f"[BybitClient] {coin} Balance: {coin_balance}")
                return coin_balance
            print("[BybitClient] No balance data returned")
            return None
        except Exception as e:
            print(f"[BybitClient] Balance error: {e}")
            return None
