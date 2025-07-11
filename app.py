# AlgoTrader Dashboard Application
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timezone, timedelta
import time
from trading_engine import TradingEngine
from dashboard_components import DashboardComponents
from data_provider import DataProvider
from utils import format_currency, format_percentage, get_status_color
from automated_trader import automated_trader
from database import db_manager
from utils import get_ticker_snapshot
from streamlit_autorefresh import st_autorefresh
from PIL import Image


# Refresh every 30 seconds (30000 milliseconds)
st_autorefresh(interval=30000, limit=None, key="tickerrefresh")

# Load the logo image
logo = Image.open("logo.png")


dashboard = DashboardComponents()
ticker_data = get_ticker_snapshot()
# ⬆️ Show at top
dashboard.render_ticker(ticker_data, position='top')

# Configure page
st.set_page_config(
    page_title="AlgoTrader",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_components():
    trading_engine = TradingEngine()
    dashboard = DashboardComponents()
    data_provider = DataProvider()
    return trading_engine, dashboard, data_provider

trading_engine, dashboard, data_provider = init_components()

# Sidebar Navigation
st.image(logo, width=50)
st.sidebar.title("🚀 AlgoTrader")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navigate",
    ["🏠 Dashboard", "📊 Signals", "💼 Portfolio", "📈 Charts", "🤖 Automation", "🗄️ Database", "⚙️ Settings"]
)

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto Refresh (60s)", value=True)
if auto_refresh:
    # Auto refresh every 60 seconds
    time.sleep(0.1)  # Small delay to prevent too frequent updates

# Manual refresh button
if st.sidebar.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# System Status
balance = trading_engine.load_capital()
daily_pnl_pct = trading_engine.today_loss_pct()
status_color = get_status_color(daily_pnl_pct)

st.sidebar.metric(
    "💰 Wallet Balance",
    f"${format_currency(balance)}",
    f"{format_percentage(daily_pnl_pct)}% today"
)

st.sidebar.markdown(f"**Status:** <span style='color: {status_color}'>{'🟢 Active' if daily_pnl_pct < trading_engine.MAX_LOSS_PCT else '🔴 Paused'}</span>", unsafe_allow_html=True)

# Automation Status in Sidebar
automation_status = automated_trader.get_automation_status()
automation_indicator = "🤖 Running" if automation_status['is_running'] else "⏸️ Stopped"
automation_color = "#00d4aa" if automation_status['is_running'] else "#ff4444"
st.sidebar.markdown(f"**Auto Mode:** <span style='color: {automation_color}'>{automation_indicator}</span>", unsafe_allow_html=True)

# Database Status
try:
    db_balance = db_manager.get_portfolio_balance()
    db_status = "🟢 Ok" if db_balance is not None else "🔴 Error"
    db_color = "#00d4aa" if db_balance is not None else "#ff4444"
    st.sidebar.markdown(f"**Database:** <span style='color: {db_color}'>{db_status}</span>", unsafe_allow_html=True)
except:
    st.sidebar.markdown(f"**Database:** <span style='color: #ff4444'>🔴 Error</span>", unsafe_allow_html=True)

# Main Content Area
if page == "🏠 Dashboard":
    st.title("🚀 AlgoTrader")
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Wallet Balance",
            f"${format_currency(balance)}",
            f"{format_percentage(daily_pnl_pct)}%"
        )
    
    # Get recent signals and trades
    recent_signals = trading_engine.get_recent_signals(limit=5)
    recent_trades = trading_engine.get_recent_trades(limit=10)
    
    with col2:
        st.metric(
            "Active Signals",
            len(recent_signals),
            "Last hour"
        )
    
    with col3:
        total_trades_today = len([t for t in recent_trades if t['timestamp'].startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))])
        st.metric(
            "Trades Today",
            total_trades_today,
            "Executed"
        )
    
    with col4:
        win_rate = trading_engine.calculate_win_rate(recent_trades)
        st.metric(
            "Win Rate",
            f"{win_rate}%",
            "Last 30 trades"
        )
    
    st.markdown("---")
    
    # Recent Signals and Performance Charts
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📡 Latest Signals")
        if recent_signals:
            for i, signal in enumerate(recent_signals[:5]):
                with st.expander(f"#{i+1} {signal['symbol']} - {signal['side']} ({signal['confidence']}%)", expanded=i==0):
                    dashboard.display_signal_card(signal)
        else:
            st.info("No recent signals available")
    
    with col2:
        st.subheader("📊 Wallet Tracker")
        if recent_trades:
            # Create performance chart
            perf_chart = dashboard.create_portfolio_performance_chart(recent_trades, balance)
            st.plotly_chart(perf_chart, use_container_width=True)
        else:
            st.info("No trade history available")
    
    


elif page == "📊 Signals":
    st.title("📊 AI Trading Signals")
    
    # Signal Generation Controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        symbol_limit = st.number_input("Symbols to Analyze", min_value=10, max_value=100, value=30)
    
    with col2:
        confidence_threshold = st.slider("Min Confidence %", min_value=50, max_value=95, value=75)
    
    with col3:
        if st.button("🔍 Scan New Signals", type="primary"):
            with st.spinner("Analyzing markets..."):
                signals = trading_engine.generate_signals(symbol_limit, confidence_threshold)
                st.success(f"Generated {len(signals)} signals")
                st.rerun()
    
    # Display Active Signals
    signals = trading_engine.get_recent_signals()
    
    if signals:
        # Filter controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            strategy_filter = st.multiselect(
                "Filter by Strategy",
                options=list(set(s['strategy'] for s in signals)),
                default=list(set(s['strategy'] for s in signals))
            )
        
        with col2:
            side_filter = st.multiselect(
                "Filter by Side",
                options=["LONG", "SHORT"],
                default=["LONG", "SHORT"]
            )
        
        with col3:
            min_score = st.slider("Minimum Score", min_value=70, max_value=100, value=80)
        
        # Apply filters
        filtered_signals = [
            s for s in signals 
            if s['strategy'] in strategy_filter 
            and s['side'] in side_filter 
            and s['score'] >= min_score
        ]
        
        st.subheader(f"📡 {len(filtered_signals)} Active Signals")
        
        # Display signals in a table
        if filtered_signals:
            dashboard.display_signals_table(filtered_signals)
            
            # Export options
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📤 Export to Discord"):
                    for signal in filtered_signals[:5]:  # Limit to top 5
                        trading_engine.post_signal_to_discord(signal)
                    st.success("Signals posted to Discord!")
            
            with col2:
                if st.button("📤 Export to Reddit"):
                    for signal in filtered_signals[:5]:
                        trading_engine.post_signal_to_reddit(signal)
                    st.success("Signals posted to Reddit!")
            
            with col3:
                if st.button("📄 Export PDF"):
                    pdf_path = trading_engine.export_signals_pdf(filtered_signals)
                    st.success(f"PDF exported: {pdf_path}")
        else:
            st.info("No signals match the current filters")
    else:
        st.info("No signals available. Generate new signals to get started.")

elif page == "💼 Portfolio":
    st.title("💼 Wallet Summary")
    
    # Portfolio Summary
    balance = trading_engine.load_capital()
    trades = trading_engine.get_recent_trades()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Balance", f"${format_currency(balance)}")
    
    with col2:
        start_balance = trading_engine.START_CAPITAL
        total_return = (balance - start_balance) / start_balance * 100
        st.metric("Total Return", f"{format_percentage(total_return)}%")
    
    with col3:
        daily_pnl = sum(t['pnl'] for t in trades if t['timestamp'].startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d")))
        st.metric("Daily P&L", f"${format_currency(daily_pnl)}")
    
    with col4:
        win_rate = trading_engine.calculate_win_rate(trades)
        st.metric("Win Rate", f"{win_rate}%")
    
    st.markdown("---")
    
    # Trade History
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Assets Analysis")
        if trades:
            perf_chart = dashboard.create_detailed_performance_chart(trades, balance)
            st.plotly_chart(perf_chart, use_container_width=True)
    
    with col2:
        st.subheader("📊 Trade Stats")
        if trades:
            stats = trading_engine.calculate_trade_statistics(trades)
            dashboard.display_trade_statistics(stats)
        else:
            st.info("No trade data available")
    
    # Recent Trades Table
    st.subheader("🔄 Recent Trades")
    if trades:
        dashboard.display_trades_table(trades)
    else:
        st.info("No trades executed yet")

elif page == "📈 Charts":
    st.title("📈 Market Analysis")
    
    # Symbol selection
    symbols = data_provider.get_popular_symbols()
    selected_symbol = st.selectbox("Select Symbol", symbols, index=0 if symbols else None)
    
    if selected_symbol:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            timeframe = st.selectbox("Timeframe", ["15m", "1h", "4h", "1d"], index=1)
        
        with col2:
            limit = st.slider("Candles", min_value=50, max_value=500, value=100)
        
        with col3:
            indicators = st.multiselect(
                "Indicators",
                [
                    "EMA 9", 
                    "EMA 21", 
                    "MA 50", 
                    "MA 200", 
                    "Bollinger Bands", 
                    "RSI", 
                    "MACD", 
                    "Stoch RSI", 
                    "Volume"
                ],
                default=["Bollinger Bands", "MA 200", "RSI","Volume"]
            )

    
    # Fetch and display chart
    with st.spinner("Loading chart data..."):
        chart_data = data_provider.get_chart_data(selected_symbol, timeframe, limit)
        
        if chart_data:
            chart = dashboard.create_technical_chart(chart_data, selected_symbol, indicators)
            st.plotly_chart(chart, use_container_width=True)
            
            # Current signal for this symbol
            current_signals = [s for s in trading_engine.get_recent_signals() if s['symbol'] == selected_symbol]
            if current_signals:
                st.subheader(f"🎯 Current Signals for {selected_symbol}")
                for signal in current_signals:
                    dashboard.display_signal_card(signal)
        else:
            st.error(f"Failed to load data for {selected_symbol}")

elif page == "🤖 Automation":
    st.title("🤖 AlgoTrading System")
    
    # Get automation status
    automation_status = automated_trader.get_automation_status()
    
    # Automation Status Display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_text = "🟢 Active" if automation_status['is_running'] else "🔴 Off"
        st.metric("Automation Status", status_text)
    
    with col2:
        st.metric("Signals Generated", automation_status['stats']['signals_generated'])
    
    with col3:
        st.metric("Trades Executed", automation_status['stats']['trades_executed'])
    
    # Control Buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not automation_status['is_running']:
            if st.button("▶️ Start Auto Mode", type="primary"):
                if automated_trader.start_automation():
                    st.success("Automation started successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to start automation")
        else:
            if st.button("⏹️ Stop Automation", type="secondary"):
                if automated_trader.stop_automation():
                    st.success("Automation stopped successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to stop automation")
    
    with col2:
        if st.button("🔄 Force Signal Scan"):
            with st.spinner("Generating signals..."):
                signals = automated_trader.generate_automated_signals()
                st.success(f"Generated {len(signals)} signals")
    
    with col3:
        if st.button("📊 View Logs"):
            # Show recent log entries
            log_file = "automated_trader.log"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = f.readlines()
                    recent_logs = logs[-20:] if len(logs) > 20 else logs
                    st.text_area("Recent Logs", "\n".join(recent_logs), height=200)
            else:
                st.info("No log file found")
    
    st.markdown("---")
    
    # Automation Settings
    st.subheader("⚙️ Automation Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Signal Generation**")
        
        signal_interval = st.slider(
            "Signal Generation Interval (minutes)",
            min_value=5,
            max_value=3600,
            value=automation_status['settings']['signal_interval'] // 3600,
            help="How often to generate new signals"
        )
        
        min_confidence = st.slider(
            "Minimum Confidence %",
            min_value=50,
            max_value=95,
            value=automation_status['settings']['min_confidence'],
            help="Only trade signals with this confidence or higher"
        )
        
        max_signals = st.slider(
            "Max Signals per Cycle",
            min_value=1,
            max_value=10,
            value=automation_status['settings']['max_signals_per_cycle'],
            help="Maximum number of signals to generate per cycle"
        )
    
    with col2:
        st.markdown("**Risk Management**")
        
        trade_execution = st.checkbox(
            "Enable Trade Execution",
            value=automation_status['settings']['trade_execution'],
            help="Execute trades automatically or just generate signals"
        )
        
        max_daily_trades = st.slider(
            "Max Daily Trades",
            min_value=1,
            max_value=150,
            value=automation_status['settings']['max_daily_trades'],
            help="Maximum number of trades per day"
        )
        
        max_position_size = st.slider(
            "Max Position Size %",
            min_value=0.5,
            max_value=20.0,
            value=float(automation_status['settings']['max_position_size_pct']),
            step=0.5,
            help="Maximum percentage of portfolio per trade"
        )
        
        max_drawdown = st.slider(
            "Max Drawdown Limit %",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=0.1,
            help="Stop trading if drawdown exceeds this percentage"
        )

    
    # Save Settings Button
    if st.button("💾 Save Automation Settings", type="primary"):
        new_settings = {
            'signal_interval': signal_interval * 60,  # Convert to seconds
            'trade_execution': trade_execution,
            'min_confidence': min_confidence,
            'max_signals': max_signals,
            'max_daily_trades': max_daily_trades,
            'max_position_size': max_position_size,
            'max_drawdown': max_drawdown
        }
        
        if automated_trader.update_settings(new_settings):
            st.success("Settings saved successfully!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Failed to save settings")
    
    # Automation Statistics
    st.subheader("📈 Automation Performance")
    
    stats = automation_status['stats']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Signals", stats['signals_generated'])
    
    with col2:
        st.metric("Total Trades", stats['trades_executed'])
    
    with col3:
        success_rate = (stats['successful_trades'] / stats['trades_executed'] * 100) if stats['trades_executed'] > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        st.metric("Total P&L", f"${format_currency(stats['total_pnl'])}")
    
    # Timing Information
    if automation_status['is_running']:
        st.subheader("⏰ Timing Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if automation_status['last_signal_generation']:
                last_gen = datetime.fromisoformat(automation_status['last_signal_generation'])
                st.info(f"Last Signal Generation: {last_gen.strftime('%Y-%m-%d %H:%M:%S')}")
        
        with col2:
            if automation_status['next_signal_generation']:
                next_gen = datetime.fromisoformat(automation_status['next_signal_generation'])
                st.info(f"Next Signal Generation: {next_gen.strftime('%Y-%m-%d %H:%M:%S')}")

elif page == "🗄️ Database":
    st.title("🗄️ Trade Journal")
    
    # Database Status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            db_balance = db_manager.get_portfolio_balance()
            db_status = "🟢 Ok" if db_balance is not None else "🔴 Error"
            st.metric("Database Status", db_status)
        except Exception as e:
            st.metric("Database Status", "🔴 Error")
            st.error(f"Database error: {str(e)}")
    
    with col2:
        try:
            trades = db_manager.get_trades(limit=1000)
            st.metric("Total Trades", len(trades))
        except:
            st.metric("Total Trades", "Error")
    
    with col3:
        try:
            signals = db_manager.get_signals(limit=1000, active_only=False)
            st.metric("Total Signals", len(signals))
        except:
            st.metric("Total Signals", "Error")
    
    st.markdown("---")
    
    # Database Statistics
    st.subheader("📊 Database Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Recent Activity**")
        
        # Recent trades
        try:
            recent_trades = db_manager.get_trades(limit=5)
            if recent_trades:
                st.write("**Last 5 Trades:**")
                for trade in recent_trades:
                    pnl_color = "🟢" if trade['pnl'] > 0 else "🔴"
                    st.write(f"{pnl_color} {trade['symbol']} - ${trade['pnl']:.2f}")
            else:
                st.info("No trades in database")
        except Exception as e:
            st.error(f"Error loading trades: {e}")
    
    with col2:
        st.markdown("**System Information**")
        
        try:
            # Wallet Balance
            balance = db_manager.get_portfolio_balance()
            st.write(f"**Wallet Balance:** ${balance:.2f}")
            
            # Daily P&L
            daily_pnl = db_manager.get_daily_pnl()
            pnl_color = "🟢" if daily_pnl >= 0 else "🔴"
            st.write(f"**Daily P&L:** {pnl_color} ${daily_pnl:.2f}")
            
            # Automation stats
            automation_stats = db_manager.get_automation_stats()
            st.write(f"**Automation Signals:** {automation_stats.get('signals_generated', 0)}")
            st.write(f"**Automation Trades:** {automation_stats.get('trades_executed', 0)}")
            
        except Exception as e:
            st.error(f"Error loading system info: {e}")
    
    st.markdown("---")
    
    # Database Operations
    st.subheader("🔧 Database Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Test Connection"):
            try:
                balance = db_manager.get_portfolio_balance()
                st.success(f"✅ Database connected successfully! Balance: ${balance:.2f}")
            except Exception as e:
                st.error(f"❌ Database connection failed: {e}")
    
    with col2:
        if st.button("📊 Refresh Stats"):
            st.rerun()
    
    with col3:
        if st.button("🔄 Migrate JSON Data"):
            try:
                db_manager.migrate_json_data()
                st.success("✅ JSON data migration completed!")
            except Exception as e:
                st.error(f"❌ Migration failed: {e}")
    
    # Database Tables Info
    st.subheader("📋 Database Tables")
    
    table_info = {
        "portfolio": "Current Wallet Balance and history",
        "trades": "All executed trades with P&L tracking",
        "signals": "Generated trading signals with analysis",
        "automation_stats": "Automation performance statistics",
        "system_settings": "Application configuration settings"
    }
    
    for table, description in table_info.items():
        with st.expander(f"📊 {table.upper()} Table"):
            st.write(f"**Description:** {description}")
            
            if table == "trades":
                try:
                    trades = db_manager.get_trades(limit=10)
                    if trades:
                        st.write("**Recent Records:**")
                        df = pd.DataFrame(trades)
                        st.dataframe(df[['symbol', 'side', 'pnl', 'strategy', 'timestamp']], use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading {table}: {e}")
            
            elif table == "signals":
                try:
                    signals = db_manager.get_signals(limit=10, active_only=False)
                    if signals:
                        st.write("**Recent Records:**")
                        df = pd.DataFrame(signals)
                        st.dataframe(df[['symbol', 'side', 'confidence', 'strategy', 'timestamp']], use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading {table}: {e}")
    
    # Advanced Options
    with st.expander("🔧 Advanced Options"):
        st.warning("⚠️ Advanced operations - use with caution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Old Signals"):
                try:
                    # This would need to be implemented in db_manager
                    st.info("Feature not yet implemented")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col2:
            if st.button("📊 Export Data"):
                try:
                    # This would export data to CSV/JSON
                    st.info("Feature not yet implemented")
                except Exception as e:
                    st.error(f"Error: {e}")

elif page == "⚙️ Settings":
    st.title("⚙️ Trading Settings")
    
    # Risk Management Settings
    st.subheader("🛡️ Risk Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_max_loss = st.slider(
            "Max Daily Loss %",
            min_value=5,
            max_value=50,
            value=trading_engine.MAX_LOSS_PCT,
            help="Trading will pause if daily loss exceeds this percentage"
        )
        
        new_tp_percent = st.slider(
            "Take Profit %",
            min_value=0.1,
            max_value=2.0,
            value=trading_engine.TP_PERCENT * 100,
            step=0.1
        ) / 100
        
        new_sl_percent = st.slider(
            "Stop Loss %",
            min_value=0.05,
            max_value=1.0,
            value=trading_engine.SL_PERCENT * 100,
            step=0.05
        ) / 100
    
    with col2:
        new_leverage = st.slider(
            "Leverage",
            min_value=1,
            max_value=50,
            value=trading_engine.LEVERAGE,
            help="Leverage multiplier for position sizing"
        )
        
        risk_per_trade = st.slider(
            "Risk per Trade %",
            min_value=0.5,
            max_value=5.0,
            value=2.0,
            step=0.1,
            help="Percentage of portfolio to risk per trade"
        )
    
    # Discord/Reddit Settings
    st.subheader("🔗 Social Media Integration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        discord_webhook = st.text_input(
            "Discord Webhook URL",
            value=os.getenv("DISCORD_WEBHOOK_URL", ""),
            type="password",
            help="Your Discord webhook URL for posting signals"
        )
        
        test_discord = st.button("Test Discord Connection")
        if test_discord and discord_webhook:
            try:
                trading_engine.test_discord_connection(discord_webhook)
                st.success("Discord connection successful!")
            except Exception as e:
                st.error(f"Discord connection failed: {e}")
    
    with col2:
        reddit_enabled = st.checkbox("Enable Reddit Posting", value=False)
        
        if reddit_enabled:
            reddit_client_id = st.text_input("Reddit Client ID", type="password")
            reddit_client_secret = st.text_input("Reddit Client Secret", type="password")
            reddit_username = st.text_input("Reddit Username")
            reddit_password = st.text_input("Reddit Password", type="password")
            subreddit_name = st.text_input("Subreddit Name", value="YourSubreddit")
    
    # Save Settings
    if st.button("💾 Save Settings", type="primary"):
        # Update trading engine settings
        trading_engine.update_settings({
            "MAX_LOSS_PCT": new_max_loss,
            "TP_PERCENT": new_tp_percent,
            "SL_PERCENT": new_sl_percent,
            "LEVERAGE": new_leverage,
            "RISK_PER_TRADE": risk_per_trade / 100
        })

         # Toggle real trading (Bybit)
        real_mode = st.checkbox("✅ Enable Real Bybit Trading", value=os.getenv("USE_REAL_TRADING", "false") == "true")
        os.environ["USE_REAL_TRADING"] = str(real_mode).lower()
        db_manager.set_setting("real_trading", real_mode, "bool")  # Optional: persist in DB   

        
        # Update environment variables
        if discord_webhook:
            os.environ["DISCORD_WEBHOOK_URL"] = discord_webhook
        
        if reddit_enabled:
            os.environ.update({
                "REDDIT_CLIENT_ID": reddit_client_id,
                "REDDIT_CLIENT_SECRET": reddit_client_secret,
                "REDDIT_USERNAME": reddit_username,
                "REDDIT_PASSWORD": reddit_password,
                "REDDIT_SUBREDDIT": subreddit_name
            })
        
        st.success("Settings saved successfully!")
        time.sleep(1)
        st.rerun()
    
    # Reset to Defaults
    if st.button("🔄 Reset to Defaults"):
        trading_engine.reset_to_defaults()
        st.success("Settings reset to defaults!")
        time.sleep(1)
        st.rerun()
    
    # System Information
    st.subheader("ℹ️ System Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Signals Directory", len(os.listdir("signals")) if os.path.exists("signals") else 0)
    
    with col2:
        st.metric("Trades Directory", len(os.listdir("trades")) if os.path.exists("trades") else 0)
    
    with col3:
        capital_file_exists = os.path.exists("capital.json")
        st.metric("Capital File", "✅ Exists" if capital_file_exists else "❌ Missing")

# Auto refresh functionality
if auto_refresh:
    time.sleep(60)
    st.rerun()
    
def main():
    pass  # App logic runs above; this is just for deployment health checks

if __name__ == "__main__":
    print("✅ Streamlit AlgoTrader app started...")
    main()
# End of app.py
# This is the main entry point for the Streamlit app.
# It initializes components, sets up the sidebar, and handles page navigation.
