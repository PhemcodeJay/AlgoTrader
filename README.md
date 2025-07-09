# 🚀 CryptoPilot - Automated Trading Dashboard

A comprehensive cryptocurrency trading system with automated signal generation, portfolio management, and real-time monitoring.

## Features

### 📊 Dashboard
- Real-time portfolio monitoring
- Trading signals display
- Portfolio performance charts
- Market overview with top cryptocurrencies

### 🤖 Automated Trading
- **Automated Signal Generation**: Generate trading signals every 5 minutes
- **Risk Management**: Built-in stop-loss, take-profit, and position sizing
- **Trade Execution**: Automatic trade simulation with P&L tracking
- **Social Media Integration**: Post signals to Discord and Reddit
- **Comprehensive Logging**: Full audit trail of all activities

### 📈 Technical Analysis
- Multiple timeframe analysis (15m, 1h, 4h)
- Technical indicators: EMA, SMA, RSI, MACD, Bollinger Bands
- Market trend detection across timeframes
- Volume analysis and breakout detection

### 💼 Portfolio Management
- Starting capital: $10.00
- Risk per trade: 2% of portfolio
- Maximum daily loss limit: 15%
- Leverage: 20x
- Take Profit: 25% | Stop Loss: 10%

## Quick Start

### 1. Start the Dashboard
```bash
streamlit run app.py --server.port 5000
```

### 2. Start Automated Trading (Optional)
```bash
python start_automation.py
```

### 3. Access the Application
Open your browser and navigate to: `http://localhost:5000`

## Navigation

- **🏠 Dashboard**: Overview of portfolio and recent signals
- **📊 Signals**: Generate and view trading signals
- **💼 Portfolio**: Performance tracking and trade history
- **📈 Charts**: Technical analysis and charting
- **🤖 Automation**: Automated trading controls and settings
- **⚙️ Settings**: System configuration and API keys

## Automation Settings

### Signal Generation
- **Interval**: 1-60 minutes (default: 5 minutes)
- **Min Confidence**: 50-95% (default: 75%)
- **Max Signals per Cycle**: 1-10 (default: 5)

### Risk Management
- **Trade Execution**: Enable/disable automatic trading
- **Max Daily Trades**: 1-50 (default: 20)
- **Max Position Size**: 0.5-20% of portfolio (default: 5%)
- **Max Drawdown Limit**: 5-50% (default: 20%)

## Data Sources

- **Primary**: Binance Futures API for real-time market data
- **Fallback**: Mock data for demonstration when API is unavailable

## File Structure

```
/
├── app.py                    # Main Streamlit dashboard
├── automated_trader.py       # Automation engine
├── trading_engine.py         # Core trading logic
├── dashboard_components.py   # UI components
├── data_provider.py          # Market data integration
├── utils.py                 # Helper functions
├── start_automation.py       # Automation starter script
├── automation_settings.json # Automation configuration
├── capital.json             # Portfolio balance (auto-generated)
├── trades_history.json      # Trade log (auto-generated)
├── automated_trader.log     # Automation logs (auto-generated)
├── signals/                 # Generated signals (auto-generated)
└── trades/                  # Trade records (auto-generated)
```

## Environment Variables (Optional)

For social media integration, set these environment variables:

```bash
# Discord Integration
export DISCORD_WEBHOOK_URL="your_discord_webhook_url"

# Reddit Integration
export REDDIT_CLIENT_ID="your_reddit_client_id"
export REDDIT_CLIENT_SECRET="your_reddit_client_secret"
export REDDIT_USERNAME="your_reddit_username"
export REDDIT_PASSWORD="your_reddit_password"
```

## Safety Features

- **Daily Loss Limits**: Trading automatically pauses if daily losses exceed 15%
- **Drawdown Protection**: Trading stops if portfolio drawdown exceeds the set limit
- **Position Size Limits**: Maximum 5% of portfolio per trade
- **Confidence Filtering**: Only trade signals with 75%+ confidence
- **Comprehensive Logging**: All activities are logged for audit and analysis

## Trading Strategies

### 1. Trend Following
- Uses EMA crossovers and trend detection
- Confidence: 90%
- Best for: Strong trending markets

### 2. Mean Reversion
- RSI oversold/overbought conditions
- Bollinger Band reversals
- Confidence: 85%
- Best for: Ranging markets

### 3. Scalping
- Volume breakouts and momentum
- Quick entries and exits
- Confidence: 80%
- Best for: High volatility periods

### 4. Short Reversal
- Overbought conditions with volume
- Counter-trend positions
- Confidence: 75%
- Best for: Market tops and corrections

## Monitoring and Control

### Dashboard Monitoring
- Real-time portfolio balance
- Daily P&L tracking
- Win rate statistics
- Trade execution status

### Automation Control
- Start/stop automation with one click
- Force signal generation
- View real-time logs
- Adjust settings on-the-fly

### Performance Analytics
- Portfolio performance charts
- Trade statistics and win rates
- Drawdown analysis
- Signal effectiveness tracking

## Support

The system includes comprehensive error handling and logging. Check the following for troubleshooting:

1. **Dashboard**: Error messages and status indicators
2. **Logs**: `automated_trader.log` for detailed activity logs
3. **Settings**: Verify API configurations and risk parameters

## Disclaimer

This is a trading simulation system for educational purposes. All trades are simulated and no real money is involved. Past performance does not guarantee future results. Always conduct your own research before making any trading decisions.