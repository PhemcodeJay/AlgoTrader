# === Part 1: Config & Setup ===
import os, json, requests, logging
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import praw  # Reddit
from dotenv import load_dotenv

load_dotenv()

CAPITAL_FILE = "capital.json"
TRADE_LOG_FILE = "trades_history.json"
SIGNAL_DIR = "signals"
TRADE_DIR = "trades"
START_CAPITAL = 10.0
MAX_LOSS_PCT = 15
TP_PERCENT = 0.25
SL_PERCENT = 0.10
LEVERAGE = 20
RISK_AMOUNT = 2

def ema(values, period):
    emas, k = [], 2 / (period + 1)
    ema_prev = sum(values[:period]) / period
    emas.append(ema_prev)
    for price in values[period:]:
        ema_prev = price * k + ema_prev * (1 - k)
        emas.append(ema_prev)
    return [None] * (period - 1) + emas

def sma(values, period):
    return [None if i < period - 1 else sum(values[i+1-period:i+1]) / period for i in range(len(values))]

def compute_rsi(closes, period=14):
    gains, losses = [], []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    if len(gains) < period: return 50
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calculate_macd(values, fast=12, slow=26, signal=9):
    ema_fast = ema(values, fast)
    ema_slow = ema(values, slow)
    macd_line = [f - s if f and s else None for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema([x for x in macd_line if x is not None], signal)
    signal_line = [None] * (len(macd_line) - len(signal_line)) + signal_line
    histogram = [m - s if m and s else None for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(values, period=20, std_dev=2):
    sma_vals = sma(values, period)
    bands = []
    for i in range(len(values)):
        if i < period - 1:
            bands.append((None, None, None))
        else:
            mean = sma_vals[i]
            std = (sum((x - mean) ** 2 for x in values[i + 1 - period:i + 1]) / period) ** 0.5
            upper = mean + std_dev * std
            lower = mean - std_dev * std
            bands.append((upper, mean, lower))
    return bands

def fetch_ohlcv(symbol, interval='1h', limit=100):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        r = requests.get(url, timeout=5)
        return [[float(x[0]), float(x[1]), float(x[2]), float(x[4]), float(x[5])] for x in r.json()]
    except Exception as e:
        print(f"[ERROR] {symbol}: {e}")
        return []

def get_symbols(limit=100):
    try:
        r = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=5)
        return [s['symbol'] for s in r.json()['symbols'] if s['contractType'] == 'PERPETUAL' and 'USDT' in s['symbol']][:limit]
    except Exception as e:
        print(f"[ERROR] Symbols: {e}")
        return []
def detect_market_trend(symbol):
    def fetch_closes(symbol, tf):
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={tf}&limit=250"
        try:
            r = requests.get(url, timeout=5)
            data = r.json()
            return [float(x[4]) for x in data if len(x) > 4]
        except Exception as e:
            print(f"[ERROR] Failed to fetch {symbol} {tf} data: {e}")
            return []

    trend_info = {}
    for tf in ['1h', '4h', '15m']:
        closes = fetch_closes(symbol, tf)
        if len(closes) < 200:
            trend_info[tf] = 'neutral'
            continue

        ema9_vals = ema(closes, 9)
        ema21_vals = ema(closes, 21)
        ma50_vals = sma(closes, 50)
        ma200_vals = sma(closes, 200)

        try:
            close = closes[-1]
            ema9 = ema9_vals[-1]
            ema21 = ema21_vals[-1]
            ma50 = ma50_vals[-1]
            ma200 = ma200_vals[-1]
        except (IndexError, TypeError):
            trend_info[tf] = 'neutral'
            continue

        if None in [close, ema9, ema21, ma50, ma200]:
            trend_info[tf] = 'neutral'
            continue

        if close > ma200 and ema9 > ema21:
            trend_info[tf] = 'bullish'
        elif close < ma200 and ema9 < ema21:
            trend_info[tf] = 'bearish'
        else:
            trend_info[tf] = 'neutral'

    return trend_info

def is_trade_allowed(side, trend_info):
    trend_votes = list(trend_info.values())
    bull = trend_votes.count('bullish')
    bear = trend_votes.count('bearish')
    if bull > bear and side == 'SHORT':
        return False
    if bear > bull and side == 'LONG':
        return False
    return True

def compute_score(s):
    score = 0
    trend_info = detect_market_trend(s['symbol'])
    bull = list(trend_info.values()).count('bullish')
    bear = list(trend_info.values()).count('bearish')
    score += 10 if bull == 3 or bear == 3 else 5 if bull == 2 or bear == 2 else 0
    if s['side'] == 'LONG' and 45 < s['rsi'] < 70: score += 10
    elif s['side'] == 'SHORT' and 30 < s['rsi'] < 55: score += 10
    if s['macd_hist'] and ((s['macd_hist'] > 0 and s['side'] == 'LONG') or (s['macd_hist'] < 0 and s['side'] == 'SHORT')):
        score += 10
    if s.get("bb_breakout"): score += 5
    if s.get("vol_spike"): score += 10
    score += s["confidence"] * 0.3
    rr = TP_PERCENT / SL_PERCENT
    score += 10 if rr >= 2 else 5 if rr >= 1.5 else 0
    return round(score, 2)

def build_signal(name, condition, confidence, regime, trend_info, close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes, side):
    if not condition: return None
    side = side.upper()
    entry = close
    liquidation = entry * (1 - 1 / LEVERAGE) if side == "LONG" else entry * (1 + 1 / LEVERAGE)
    sl_price = max(entry * (1 - SL_PERCENT), liquidation * 1.05) if side == "LONG" else min(entry * (1 + SL_PERCENT), liquidation * 0.95)
    tp_price = entry * (1 + TP_PERCENT) if side == "LONG" else entry * (1 - TP_PERCENT)
    risk_per_unit = abs(entry - sl_price)
    position_size = round(RISK_AMOUNT / risk_per_unit, 6) if risk_per_unit > 0 else 0
    forecast_pnl = round((TP_PERCENT * 100 * confidence) / 100, 2)
    macd_hist_value = round(macd_hist[-1], 4) if macd_hist and macd_hist[-1] is not None else None
    signal = {
        "symbol": symbol,
        "timeframe": tf,
        "side": side,
        "entry": round(entry, 6),
        "sl": round(sl_price, 6),
        "tp": round(tp_price, 6),
        "liquidation": round(liquidation, 6),
        "rsi": rsi,
        "macd_hist": macd_hist_value,
        "trend": "bullish" if side == "LONG" else "bearish",
        "regime": regime,
        "confidence": confidence,
        "position_size": position_size,
        "forecast_pnl": forecast_pnl,
        "strategy": name,
        "timestamp": (datetime.now(timezone.utc) + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M UTC+3"),
        "vol_spike": (volumes[-1] > sum(volumes[-20:]) / 20 * 1.5) if len(volumes) >= 20 else False
    }
    signal["score"] = compute_score(signal)
    return signal
def analyze(symbol, tf="1h"):
    data = fetch_ohlcv(symbol, tf)
    if len(data) < 60: return []
    highs = [x[1] for x in data]
    lows = [x[2] for x in data]
    closes = [x[3] for x in data]
    volumes = [x[4] for x in data]
    close = closes[-1]
    ema9 = ema(closes, 9)
    ema21 = ema(closes, 21)
    ma20 = sma(closes, 20)
    ma200 = sma(closes, 200)
    rsi = compute_rsi(closes)
    bb_upper, bb_mid, bb_lower = zip(*calculate_bollinger_bands(closes))
    macd_line, macd_signal, macd_hist = calculate_macd(closes)
    trend_info = detect_market_trend(symbol)

    if any(x is None for x in [ema9[-1], ema21[-1], macd_hist[-1], bb_upper[-1], bb_lower[-1]]):
        return []

    if None in (ma20[-1], ma200[-1]):
        return []

    if rsi is None:
        return []

    regime = "trend" if ma20[-1] > ma200[-1] else (
        "mean_reversion" if rsi < 35 or rsi > 65 else "scalp"
    )


    signals = []

    if regime == "trend":
        sig = build_signal("Trend", ema9[-1] > ema21[-1], 90, regime, trend_info, close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes, "long")
        if sig: signals.append(sig)

    if regime == "mean_reversion":
        sig = build_signal("Mean-Reversion", rsi < 40 or close < ma20[-1], 85, regime, trend_info, close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes, "long")
        if sig: signals.append(sig)

    if regime == "scalp" and volumes[-1] > sum(volumes[-20:]) / 20 * 1.5:
        sig = build_signal("Scalp Breakout", True, 80, regime, trend_info, close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes, "long")
        if sig: signals.append(sig)

    if rsi > 65 and close > bb_upper[-1]:
        sig = build_signal("Short Reversal", True, 75, "reversal", trend_info, close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes, "short")
        if sig: signals.append(sig)

    if close > bb_upper[-1]:
        sig = build_signal("Bollinger Upper Breakout", True, 70, "breakout", trend_info, close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes, "long")
        if sig:
            sig["bb_breakout"] = "UPPER"
            signals.append(sig)

    if close < bb_lower[-1]:
        sig = build_signal("Bollinger Lower Breakout", True, 70, "breakout", trend_info, close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes, "short")
        if sig:
            sig["bb_breakout"] = "LOWER"
            signals.append(sig)

    return signals

# === VIRTUAL TRADER ===
class VirtualTrader:
    def __init__(self):
        self.wallet = self.load_virtual_wallet()

    def load_virtual_wallet(self):
        if not os.path.exists("virtual_wallet.json"):
            return {"balance": 100.0, "trades": []}
        with open("virtual_wallet.json") as f:
            return json.load(f)

    def save_virtual_wallet(self):
        with open("virtual_wallet.json", "w") as f:
            json.dump(self.wallet, f, indent=2)

    def execute_virtual_trade(self, signal):
        entry, tp = signal['entry'], signal['tp']
        side = signal['side']
        capital = self.wallet["balance"]
        risk_amount = capital * 0.02
        risk_per_unit = abs(entry - signal["sl"])
        qty = round(risk_amount / risk_per_unit, 4) if risk_per_unit else 0
        pnl = round((tp - entry) * qty if side == "LONG" else (entry - tp) * qty, 4)
        self.wallet["balance"] += pnl
        trade = {
            "symbol": signal["symbol"],
            "entry": entry,
            "exit": tp,
            "side": side,
            "qty": qty,
            "pnl": pnl,
            "strategy": signal["strategy"],
            "timestamp": signal["timestamp"],
            "mode": "VIRTUAL"
        }
        self.wallet["trades"].append(trade)
        self.save_virtual_wallet()
        return trade

virtual_trader = VirtualTrader()
# === TRADE EXECUTION ===
try:
    from binance.client import Client
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
    BINANCE_LIVE = BINANCE_API_KEY and BINANCE_API_SECRET
    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET) if BINANCE_LIVE else None
except:
    BINANCE_LIVE = False
    client = None

def execute_trade(signal):
    entry, tp = signal['entry'], signal['tp']
    side = signal['side']
    timestamp = signal['timestamp']
    capital = load_capital()
    risk_amount = capital * 0.02
    risk_per_unit = abs(entry - signal['sl'])
    qty = round(risk_amount / risk_per_unit, 3) if risk_per_unit > 0 else 0
    pnl, mode = 0, "VIRTUAL"

    if BINANCE_LIVE:
        try:
            order_side = Client.SIDE_BUY if side == "LONG" else Client.SIDE_SELL
            order = client.futures_create_order(
                symbol=signal['symbol'],
                side=order_side,
                type=Client.ORDER_TYPE_MARKET,
                quantity=qty
            )
            mode = "REAL"
        except Exception as e:
            print("❌ Binance Error:", e)

    trade = virtual_trader.execute_virtual_trade(signal)
    trade["mode"] = mode
    save_trade_log(trade)
    save_capital(virtual_trader.wallet["balance"])
    return trade

# === TRADE LOGGING ===
def save_trade_log(trade):
    trades = []
    if os.path.exists(TRADE_LOG_FILE):
        try:
            with open(TRADE_LOG_FILE, "r") as f:
                trades = json.load(f)
        except Exception:
            trades = []
    trades.append(trade)
    with open(TRADE_LOG_FILE, "w") as f:
        json.dump(trades, f, indent=2)

# === CAPITAL MANAGEMENT ===
def load_capital():
    if not os.path.exists(CAPITAL_FILE):
        return START_CAPITAL
    with open(CAPITAL_FILE) as f:
        try:
            data = json.load(f)
            return data.get("capital", START_CAPITAL)
        except Exception:
            return START_CAPITAL

def save_capital(capital):
    with open(CAPITAL_FILE, "w") as f:
        json.dump({"capital": capital}, f, indent=2)

# === UTILITIES ===
def format_signal(signal):
    color = "🟢" if signal.get("side") == "LONG" else "🔴"
    breakout = signal.get("bb_breakout", "")
    bb_text = f"\n📈 BB Breakout: {breakout}" if breakout else ""
    return (
        f"{color} **{signal.get('symbol')} - {signal.get('strategy')}**\n"
        f"➡️ Side: `{signal.get('side')}`\n"
        f"💵 Entry: `{signal.get('entry')}` | 🎯 TP: `{signal.get('tp')}` | 🛡️ SL: `{signal.get('sl')}`\n"
        f"📊 RSI: `{signal.get('rsi')}` | 📉 MACD Hist: `{signal.get('macd_hist')}`\n"
        f"🔥 Score: `{signal.get('score')}` | 💯 Confidence: `{signal.get('confidence')}`\n"
        f"🧠 Strategy: `{signal.get('strategy')}` | 🕒 {signal.get('timestamp')}{bb_text}"
    )

def save_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def save_pdf(filename, data, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.ln(10)
    for item in data:
        for k, v in item.items():
            pdf.cell(0, 8, f"{k}: {v}", ln=True)
        pdf.ln(4)
    pdf.output(filename)
# === DISCORD / REDDIT POSTING ===
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
REDDIT_CREDS = {
    "client_id": os.getenv("REDDIT_CLIENT_ID"),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
    "username": os.getenv("REDDIT_USERNAME"),
    "password": os.getenv("REDDIT_PASSWORD"),
    "user_agent": "AlgoTraderBot/1.0"
}
REDDIT_SUBREDDITS = os.getenv("REDDIT_SUBREDDIT", "algotrading").split(",")

# Ensure directories exist
for d in [SIGNAL_DIR, TRADE_DIR]:
    os.makedirs(d, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO)

def post_to_discord(message):
    if not DISCORD_WEBHOOK_URL:
        logging.error("Discord webhook URL is not set.")
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    except Exception as e:
        logging.error(f"Discord error: {e}")

def post_to_reddit(title, body):
    try:
        reddit = praw.Reddit(**REDDIT_CREDS)
        subreddit_name = REDDIT_SUBREDDITS[0] if REDDIT_SUBREDDITS else "algotrading"
        subreddit = reddit.subreddit(subreddit_name)
        subreddit.submit(title, selftext=body)
    except Exception as e:
        logging.error(f"Reddit error: {e}")

# === MAIN EXECUTION LOOP ===
def main(limit=100, tf="1h", export_pdf=False):
    symbols = get_symbols(limit)
    logging.info(f"Running analysis on {len(symbols)} symbols...")

    all_signals = []
    for i, sym in enumerate(symbols):
        logging.info(f"[{i+1}/{len(symbols)}] Analyzing: {sym}")
        try:
            signals = analyze(sym, tf)
            if signals:
                all_signals.extend(signals)
        except Exception as e:
            logging.error(f"Error analyzing {sym}: {e}")

    if not all_signals:
        logging.info("No signals found.")
        return

    # Sort signals by score
    sorted_signals = sorted(all_signals, key=lambda x: x['score'], reverse=True)

    # Log top 20
    logging.info("\nTop 20 Signals:")
    for s in sorted_signals[:20]:
        logging.info(format_signal(s))

    # Trade top 5
    top_trades = sorted_signals[:5]
    for sig in top_trades:
        try:
            filename = sig['symbol'] + "_" + sig['timestamp'].replace(" ", "_")
            save_json(sig, os.path.join(SIGNAL_DIR, f"{filename}.json"))
            post_to_discord(format_signal(sig))
            post_to_reddit(f"New Signal: {sig['symbol']} {sig['side']}", format_signal(sig))

            trade = execute_trade(sig)
            logging.info(f"Executed trade: {trade}")
            save_json(trade, os.path.join(TRADE_DIR, f"{filename}.json"))
        except Exception as e:
            logging.error(f"Error trading {sig['symbol']}: {e}")

    if export_pdf:
        pdf_file = f"signals_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        save_pdf(pdf_file, sorted_signals[:20], title="Top 20 Signal Report")
        logging.info(f"Exported PDF: {pdf_file}")

    logging.info("Run complete.")

if __name__ == "__main__":
    main(limit=100, tf="1h", export_pdf=True)
# This is the main entry point for the bot. You can run this script to start the analysis and trading process.