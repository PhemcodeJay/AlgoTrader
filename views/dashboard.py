import streamlit as st
from datetime import datetime, timezone

from db import Signal  # ✅ Correct import for the Signal model

def render(trading_engine, dashboard, db_manager):
    st.title("🚀 AlgoTrader Dashboard")

    balance = trading_engine.load_capital()
    daily_pnl_pct = trading_engine.get_daily_pnl()
    recent_trades = trading_engine.get_recent_trades(limit=10)

    # ✅ Use the imported Signal model directly
    with db_manager.get_session() as session:
        signal_objs = session.query(Signal).order_by(Signal.created_at.desc()).limit(5).all()
        recent_signals = [s.to_dict() for s in signal_objs]

    # === KPI Row ===
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Wallet Balance", f"${balance['capital']:.2f}", f"{daily_pnl_pct:.2f}%")
    col2.metric("Active Signals", len(recent_signals), "Last hour")
    col3.metric("Trades Today", len([
        t for t in recent_trades if t["timestamp"].startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ]))
    
    st.markdown("---")

    # === Latest Signals & Portfolio Chart ===
    left, right = st.columns([1, 1])

    with left:
        st.subheader("📡 Latest Signals")
        if recent_signals:
            for i, signal in enumerate(recent_signals):
                with st.expander(f"{signal['symbol']} - {signal['signal_type']} ({signal['score']}%)", expanded=i == 0):
                    dashboard.display_signal_card(signal)
        else:
            st.info("No recent signals available")

    with right:
        st.subheader("📊 Wallet Tracker")
        if recent_trades:
            fig = dashboard.create_portfolio_performance_chart(recent_trades, balance)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trade history available")
