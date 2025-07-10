# AlgoTrader Dashboard

## Overview

AlgoTrader is a cryptocurrency trading dashboard built with Streamlit that provides real-time trading signals, portfolio management, and charting capabilities. The application integrates with Binance API for market data and includes automated trading signal generation with social media posting capabilities.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application
- **Visualization**: Plotly for interactive charts and graphs
- **Layout**: Multi-page dashboard with sidebar navigation
- **Components**: Modular dashboard components for reusable UI elements

### Backend Architecture
- **Trading Engine**: Core logic for signal generation, portfolio management, and risk calculation
- **Data Provider**: Binance API integration for real-time market data
- **Signal Processing**: Technical analysis and trading strategy implementation
- **Database Storage**: PostgreSQL database for persistent data storage
- **Automated Trading**: Background automation engine with threading support

### Data Sources
- **Primary**: Binance Futures API for OHLCV data and market information
- **Secondary**: PostgreSQL database for persistent storage of trades, signals, and settings
- **Fallback**: Mock data for demonstration when external APIs are unavailable

## Key Components

### Core Modules

1. **app.py** - Main Streamlit application entry point
   - Multi-page navigation (Dashboard, Signals, Portfolio, Charts, Automation, Database, Settings)
   - Auto-refresh functionality with 30-second intervals
   - Component initialization and caching
   - Database integration and status monitoring

2. **trading_engine.py** - Core trading logic
   - Portfolio balance management
   - Risk management with 2% risk per trade
   - Signal generation and trade execution logic
   - Social media integration (Discord, Reddit)
   - PDF report generation capabilities

3. **dashboard_components.py** - UI component library
   - Signal card displays with confidence indicators
   - Data table rendering for signals
   - Reusable visualization components

4. **data_provider.py** - External data integration
   - Binance API wrapper for market data
   - Popular symbols filtering (top 20 USDT pairs)
   - OHLCV data retrieval for charting

5. **utils.py** - Helper functions
   - Currency and percentage formatting
   - Color coding for P&L indicators
   - Risk-reward ratio calculations

6. **database.py** - Database management system
   - PostgreSQL integration with SQLAlchemy ORM
   - Database models for trades, signals, portfolio, and automation stats
   - Data migration utilities from JSON files
   - Connection management and error handling

7. **automated_trader.py** - Automated trading system
   - Background signal generation every 5 minutes
   - Risk management and position sizing
   - Trade execution automation
   - Performance tracking and statistics

### Trading Configuration
- **Starting Capital**: $10.00
- **Maximum Loss**: 15% of capital
- **Take Profit**: 25% target
- **Stop Loss**: 10% risk
- **Leverage**: 20x
- **Risk Per Trade**: 2% of portfolio

## Data Flow

1. **Market Data Ingestion**: Binance API → Data Provider → Trading Engine
2. **Signal Generation**: Trading Engine processes market data → Generates signals with confidence scores
3. **Risk Assessment**: Signals evaluated against portfolio balance and risk parameters
4. **Display Layer**: Dashboard Components render signals and portfolio data
5. **Social Sharing**: Qualified signals posted to Discord/Reddit channels
6. **Trade Logging**: All activities recorded in JSON files for historical analysis

## External Dependencies

### Required Libraries
- **streamlit**: Web application framework
- **plotly**: Interactive charting and visualization
- **pandas**: Data manipulation and analysis
- **requests**: HTTP client for API calls
- **fpdf**: PDF report generation
- **praw**: Reddit API integration

### External Services
- **Binance Futures API**: Real-time market data and trading information
- **Discord Webhooks**: Automated signal posting
- **Reddit API**: Community engagement and signal sharing

### Environment Variables
- `DISCORD_WEBHOOK_URL`: Discord channel webhook for notifications
- `REDDIT_CLIENT_ID`: Reddit application client ID
- `REDDIT_CLIENT_SECRET`: Reddit application secret
- `REDDIT_USERNAME`: Reddit account username
- `REDDIT_PASSWORD`: Reddit account password

## Deployment Strategy

### Local Development
- Streamlit development server with auto-reload
- File-based storage for rapid prototyping
- Environment variable configuration for API keys

### Production Considerations
- Requires persistent storage for trade history and capital tracking
- API rate limiting management for Binance endpoints
- Secure credential management for social media integrations
- Consider migrating to database storage for scalability

### File Structure
```
/
├── app.py                    # Main application
├── trading_engine.py         # Core trading logic
├── dashboard_components.py   # UI components
├── data_provider.py          # External data integration
├── utils.py                  # Helper functions
├── database.py               # Database management
├── automated_trader.py       # Automation engine
├── start_automation.py       # Automation starter script
├── automation_settings.json # Automation configuration
├── automated_trader.log     # Automation logs (generated)
├── capital.json             # Portfolio balance (legacy/backup)
├── trades_history.json      # Trade log (legacy/backup)
├── signals/                 # Signal files (legacy/backup)
└── trades/                  # Trade records (legacy/backup)
```

## Recent Changes

### Database Integration & Automated Trading System (July 08, 2025)
- **PostgreSQL Database**: Migrated from JSON files to PostgreSQL for persistent storage
- **Database Models**: Created comprehensive models for trades, signals, portfolio, and automation stats
- **Data Migration**: Automatic migration from existing JSON files to database
- **Database Dashboard**: New database management interface with connection monitoring
- **Automated Signal Generation**: Added `automated_trader.py` with background signal generation every 5 minutes
- **Risk Management Integration**: Comprehensive risk controls including daily loss limits, drawdown protection, and position sizing
- **Dashboard Automation Tab**: New interface for controlling and monitoring automated trading
- **Threading Support**: Background automation runs independently of the dashboard
- **Comprehensive Logging**: Full audit trail with `automated_trader.log` for all automation activities
- **Settings Persistence**: Database-based configuration storage for automation parameters

### Technical Implementation Details
- **AutomatedTrader Class**: Core automation engine with threading support
- **Risk Validation**: Multi-level risk checks before each trade execution
- **Performance Tracking**: Real-time statistics on signal generation and trade execution
- **Graceful Shutdown**: Proper cleanup and thread management
- **Social Media Integration**: Automated posting to Discord and Reddit

### User Interface Enhancements
- **Automation Status Indicator**: Real-time status in sidebar
- **Control Panel**: Start/stop automation with one click
- **Performance Metrics**: Success rates, P&L tracking, and timing information
- **Settings Management**: Dynamic configuration updates without restart
- **Log Viewer**: Built-in log viewing for troubleshooting

## Changelog

- July 08, 2025. Initial setup and automated trading system implementation

## User Preferences

Preferred communication style: Simple, everyday language.