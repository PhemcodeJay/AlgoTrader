import os
import json
import requests
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import praw
from database import db_manager

class TradingEngine:
    def __init__(self):
        # Configuration
        self.CAPITAL_FILE = "capital.json"
        self.TRADE_LOG_FILE = "trades_history.json"
        self.SIGNAL_DIR = "signals"
        self.TRADE_DIR = "trades"
        self.START_CAPITAL = 10.0
        self.MAX_LOSS_PCT = 15
        self.TP_PERCENT = 0.25
        self.SL_PERCENT = 0.10
        self.LEVERAGE = 20
        self.RISK_PER_TRADE = 0.02  # 2% risk per trade
        
        # Create directories
        for d in [self.SIGNAL_DIR, self.TRADE_DIR]:
            os.makedirs(d, exist_ok=True)
        
        # Social media configuration
        self.DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
        self.REDDIT_CREDS = {
            "client_id": os.getenv("REDDIT_CLIENT_ID", ""),
            "client_secret": os.getenv("REDDIT_CLIENT_SECRET", ""),
            "username": os.getenv("REDDIT_USERNAME", ""),
            "password": os.getenv("REDDIT_PASSWORD", ""),
            "user_agent": "cryptopilot_bot"
        }
    
    def load_capital(self):
        """Load current portfolio balance"""
        return db_manager.get_portfolio_balance()
    
    def save_capital(self, balance):
        """Save portfolio balance"""
        db_manager.update_portfolio_balance(round(balance, 4))
    
    def log_trade(self, trade):
        """Log a trade to history"""
        db_manager.add_trade(trade)
    
    def today_loss_pct(self):
        """Calculate today's loss percentage"""
        daily_pnl = db_manager.get_daily_pnl()
        capital = self.load_capital()
        if capital > 0 and daily_pnl < 0:
            return round(-daily_pnl / capital * 100, 2)
        return 0
    
    def get_recent_signals(self, limit=10):
        """Get recent trading signals"""
        return db_manager.get_signals(limit=limit)
    
    def get_recent_trades(self, limit=50):
        """Get recent trades from history"""
        return db_manager.get_trades(limit=limit)
    
    def calculate_win_rate(self, trades):
        """Calculate win rate from trades"""
        if not trades:
            return 0
        
        winning_trades = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
        return round(winning_trades / len(trades) * 100, 1)
    
    def calculate_trade_statistics(self, trades):
        """Calculate comprehensive trade statistics"""
        if not trades:
            return {}
        
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(len(winning_trades) / total_trades * 100, 1),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0
        }
    
    def generate_signals(self, symbol_limit=30, confidence_threshold=75):
        """Generate new trading signals"""
        symbols = self.get_symbols(limit=symbol_limit)
        all_signals = []
        
        for symbol in symbols:
            try:
                signals = self.analyze(symbol)
                # Filter by confidence
                filtered_signals = [s for s in signals if s.get('confidence', 0) >= confidence_threshold]
                all_signals.extend(filtered_signals)
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                continue
        
        # Sort by score and save top signals
        top_signals = sorted(all_signals, key=lambda x: (x.get('score', 0), x.get('confidence', 0)), reverse=True)[:10]
        
        # Save signals to database
        for signal in top_signals:
            db_manager.add_signal(signal)
        
        return top_signals
    
    def get_symbols(self, limit=100):
        """Get list of trading symbols from Binance"""
        try:
            r = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=10)
            r.raise_for_status()
            symbols = [s['symbol'] for s in r.json()['symbols'] 
                      if s['contractType'] == 'PERPETUAL' and 'USDT' in s['symbol']]
            return symbols[:limit]
        except Exception as e:
            print(f"Error fetching symbols: {e}")
            # Return some popular symbols as fallback
            return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'DOGEUSDT']
    
    def fetch_ohlcv(self, symbol, interval='1h', limit=100):
        """Fetch OHLCV data from Binance"""
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            # Return [high, low, close, volume, open]
            return [[float(x[2]), float(x[3]), float(x[4]), float(x[5]), float(x[1])] for x in data]
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")
            return []
    
    def ema(self, values, period):
        """Calculate Exponential Moving Average"""
        if len(values) < period:
            return [None] * len(values)
        
        emas = []
        k = 2 / (period + 1)
        ema_prev = sum(values[:period]) / period
        emas.extend([None] * (period - 1))
        emas.append(ema_prev)
        
        for price in values[period:]:
            ema_prev = price * k + ema_prev * (1 - k)
            emas.append(ema_prev)
        
        return emas
    
    def sma(self, values, period):
        """Calculate Simple Moving Average"""
        return [None if i < period - 1 else sum(values[i+1-period:i+1]) / period 
                for i in range(len(values))]
    
    def compute_rsi(self, closes, period=14):
        """Calculate RSI"""
        if len(closes) < period + 1:
            return 50
        
        gains, losses = [], []
        for i in range(1, len(closes)):
            delta = closes[i] - closes[i - 1]
            gains.append(max(delta, 0))
            losses.append(max(-delta, 0))
        
        if len(gains) < period:
            return 50
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)
    
    def calculate_macd(self, values, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = self.ema(values, fast)
        ema_slow = self.ema(values, slow)
        
        macd_line = [f - s if f and s else None for f, s in zip(ema_fast, ema_slow)]
        
        # Filter out None values for signal line calculation
        macd_values = [x for x in macd_line if x is not None]
        if len(macd_values) < signal:
            signal_line = [None] * len(macd_line)
            histogram = [None] * len(macd_line)
        else:
            signal_line_values = self.ema(macd_values, signal)
            signal_line = [None] * (len(macd_line) - len(signal_line_values)) + signal_line_values
            histogram = [m - s if m and s else None for m, s in zip(macd_line, signal_line)]
        
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(self, values, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma_vals = self.sma(values, period)
        bands = []
        
        for i in range(len(values)):
            if i < period - 1:
                bands.append((None, None, None))
            else:
                mean = sma_vals[i]
                variance = sum((x - mean) ** 2 for x in values[i + 1 - period:i + 1]) / period
                std = variance ** 0.5
                upper = mean + std_dev * std
                lower = mean - std_dev * std
                bands.append((upper, mean, lower))
        
        return bands
    
    def detect_market_trend(self, symbol):
        """Detect market trend across multiple timeframes"""
        trend_info = {}
        
        for tf in ['1h', '4h', '15m']:
            data = self.fetch_ohlcv(symbol, tf, 60)
            if not data or len(data) < 50:
                trend_info[tf] = 'neutral'
                continue
            
            closes = [x[2] for x in data]  # close prices
            ema9 = self.ema(closes, 9)
            ema21 = self.ema(closes, 21)
            ma200 = self.sma(closes, 50)
            
            if not ema9[-1] or not ema21[-1] or not ma200[-1]:
                trend_info[tf] = 'neutral'
                continue
            
            close = closes[-1]
            
            if close > ma200[-1] and ema9[-1] > ema21[-1]:
                trend_info[tf] = 'bullish'
            elif close < ma200[-1] and ema9[-1] < ema21[-1]:
                trend_info[tf] = 'bearish'
            else:
                trend_info[tf] = 'neutral'
        
        return trend_info
    
    def is_trade_allowed(self, side, trend_info):
        """Check if trade is allowed based on trend"""
        trend_votes = list(trend_info.values())
        bull = trend_votes.count('bullish')
        bear = trend_votes.count('bearish')
        
        if bull > bear and side == 'SHORT':
            return False
        if bear > bull and side == 'LONG':
            return False
        
        return True
    
    def build_signal(self, name, condition, confidence, regime, trend_info, close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes):
        """Build a trading signal"""
        if not condition:
            return None
        
        side = "LONG" if name != "Short Reversal" else "SHORT"
        
        if not self.is_trade_allowed(side, trend_info):
            return None
        
        entry = close
        sl_price = entry * (1 - self.SL_PERCENT) if side == "LONG" else entry * (1 + self.SL_PERCENT)
        tp_price = entry * (1 + self.TP_PERCENT) if side == "LONG" else entry * (1 - self.TP_PERCENT)
        liquidation = entry * (1 - 1 / self.LEVERAGE) if side == "LONG" else entry * (1 + 1 / self.LEVERAGE)
        
        signal = {
            "symbol": symbol,
            "timeframe": tf,
            "side": side,
            "entry": round(entry, 6),
            "sl": round(sl_price, 6),
            "tp": round(tp_price, 6),
            "liquidation": round(liquidation, 6),
            "rsi": rsi,
            "macd_hist": round(macd_hist[-1], 4) if macd_hist and macd_hist[-1] else None,
            "bb_breakout": "YES" if (bb_upper and bb_lower and (close > bb_upper[-1] or close < bb_lower[-1])) else "NO",
            "trend": "bullish" if side == "LONG" else "bearish",
            "regime": regime,
            "confidence": confidence,
            "score": 80 + confidence * 0.2,
            "strategy": name,
            "timestamp": (datetime.now(timezone.utc) + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M UTC+3"),
            "vol_spike": volumes[-1] > sum(volumes[-20:]) / 20 * 1.5 if len(volumes) >= 20 else False
        }
        
        return signal
    
    def analyze(self, symbol, tf="1h"):
        """Analyze a symbol and generate signals"""
        data = self.fetch_ohlcv(symbol, tf)
        if len(data) < 60:
            return []
        
        highs = [x[0] for x in data]
        lows = [x[1] for x in data]
        closes = [x[2] for x in data]
        volumes = [x[3] for x in data]
        
        close = closes[-1]
        
        # Calculate indicators
        ema9 = self.ema(closes, 9)
        ema21 = self.ema(closes, 21)
        ma20 = self.sma(closes, 20)
        ma200 = self.sma(closes, 50)
        rsi = self.compute_rsi(closes)
        
        bb_bands = self.calculate_bollinger_bands(closes)
        bb_upper, bb_mid, bb_lower = zip(*bb_bands) if bb_bands else ([], [], [])
        
        macd_line, macd_signal, macd_hist = self.calculate_macd(closes)
        
        trend_info = self.detect_market_trend(symbol)
        
        # Determine regime
        if ma20 and ma200 and ma20[-1] and ma200[-1]:
            if ma20[-1] > ma200[-1]:
                regime = "trend"
            elif rsi < 35 or rsi > 65:
                regime = "mean_reversion"
            else:
                regime = "scalp"
        else:
            regime = "scalp"
        
        signals = []
        
        # Generate signals based on regime
        if regime == "trend" and ema9 and ema21 and ema9[-1] and ema21[-1]:
            sig = self.build_signal("Trend", ema9[-1] > ema21[-1], 90, regime, trend_info, 
                                  close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes)
            if sig:
                signals.append(sig)
        
        if regime == "mean_reversion":
            condition = rsi < 40 or (ma20 and ma20[-1] and close < ma20[-1])
            sig = self.build_signal("Mean-Reversion", condition, 85, regime, trend_info,
                                  close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes)
            if sig:
                signals.append(sig)
        
        if regime == "scalp" and len(volumes) >= 20 and volumes[-1] > sum(volumes[-20:]) / 20 * 1.5:
            sig = self.build_signal("Scalp Breakout", True, 80, regime, trend_info,
                                  close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes)
            if sig:
                signals.append(sig)
        
        if rsi > 65 and bb_upper and bb_upper[-1] and close > bb_upper[-1]:
            sig = self.build_signal("Short Reversal", True, 75, "reversal", trend_info,
                                  close, symbol, tf, rsi, macd_hist, bb_upper, bb_lower, volumes)
            if sig:
                signals.append(sig)
        
        return signals
    
    def simulate_trade(self, signal):
        """Simulate executing a trade"""
        entry, tp = signal['entry'], signal['tp']
        side = signal['side']
        capital = self.load_capital()
        
        # Calculate position size based on risk
        risk_amount = capital * self.RISK_PER_TRADE
        risk_per_unit = abs(signal['entry'] - signal['sl'])
        qty = round(risk_amount / risk_per_unit, 4) if risk_per_unit > 0 else 0
        
        # Calculate PnL
        pnl = round((tp - entry) * qty if side == "LONG" else (entry - tp) * qty, 4)
        
        # Update capital
        capital += pnl
        self.save_capital(capital)
        
        # Create trade record
        trade = {
            "symbol": signal["symbol"],
            "side": side,
            "entry": entry,
            "exit": tp,
            "qty": qty,
            "pnl": pnl,
            "strategy": signal["strategy"],
            "timestamp": signal["timestamp"]
        }
        
        self.log_trade(trade)
        return trade
    
    def post_signal_to_discord(self, signal):
        """Post signal to Discord"""
        if not self.DISCORD_WEBHOOK_URL:
            raise Exception("Discord webhook URL not configured")
        
        message = self.format_signal_message(signal)
        try:
            response = requests.post(self.DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"Discord posting failed: {e}")
    
    def post_signal_to_reddit(self, signal):
        """Post signal to Reddit"""
        if not all(self.REDDIT_CREDS.values()):
            raise Exception("Reddit credentials not configured")
        
        try:
            reddit = praw.Reddit(**self.REDDIT_CREDS)
            subreddit = reddit.subreddit(os.getenv("REDDIT_SUBREDDIT", "YourSubreddit"))
            title = f"CryptoPilot Signal - {signal['symbol']} {signal['side']}"
            body = self.format_signal_message(signal)
            subreddit.submit(title, selftext=body)
        except Exception as e:
            raise Exception(f"Reddit posting failed: {e}")
    
    def format_signal_message(self, signal):
        """Format signal for social media posting"""
        return f"""📈 {signal['symbol']} [{signal['side']}] | {signal['strategy']}
Entry: {signal['entry']} | TP: {signal['tp']} | SL: {signal['sl']}
Confidence: {signal['confidence']}% | Score: {signal['score']}
Regime: {signal['regime']} | Trend: {signal['trend']}
Timestamp: {signal['timestamp']}"""
    
    def export_signals_pdf(self, signals):
        """Export signals to PDF"""
        filename = f"signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "CryptoPilot Trading Signals", ln=True, align="C")
        pdf.ln(5)
        
        for signal in signals:
            for k, v in signal.items():
                pdf.multi_cell(0, 8, f"{k}: {v}")
            pdf.ln(5)
        
        pdf.output(filename)
        return filename
    
    def test_discord_connection(self, webhook_url):
        """Test Discord webhook connection"""
        test_message = "🧪 CryptoPilot Dashboard - Connection Test"
        response = requests.post(webhook_url, json={"content": test_message}, timeout=10)
        response.raise_for_status()
    
    def update_settings(self, settings):
        """Update trading settings"""
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def reset_to_defaults(self):
        """Reset settings to default values"""
        self.MAX_LOSS_PCT = 15
        self.TP_PERCENT = 0.25
        self.SL_PERCENT = 0.10
        self.LEVERAGE = 20
        self.RISK_PER_TRADE = 0.02
