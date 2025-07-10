import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from datetime import datetime, timezone
from utils import format_currency, format_percentage, get_trend_color
from trading_engine import TradingEngine


class DashboardComponents:
    def __init__(self, engine=None):
        self.engine = engine or TradingEngine()
    
    def display_signal_card(self, signal):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{signal['symbol']}** - {signal['side']}")
            st.markdown(f"Strategy: {signal['strategy']}")
            st.markdown(f"Entry: ${signal['entry']}")
            st.markdown(f"TP: ${signal['tp']} | SL: ${signal['sl']}")
        with col2:
            confidence_color = (
                "green" if signal['confidence'] >= 85 else
                "orange" if signal['confidence'] >= 75 else
                "red"
            )
            st.markdown(
                f"<div style='background-color: {confidence_color}; color: white; "
                f"padding: 5px; border-radius: 5px; text-align: center;'>"
                f"{signal['confidence']}% Confidence</div>", 
                unsafe_allow_html=True
            )
            st.markdown(f"Score: {signal['score']}")
            st.markdown(f"RSI: {signal['rsi']}")

    def display_signals_table(self, signals):
        df_data = [{
            'Symbol': s['symbol'], 'Side': s['side'], 'Strategy': s['strategy'],
            'Entry': f"${s['entry']}", 'TP': f"${s['tp']}", 'SL': f"${s['sl']}",
            'Confidence': f"{s['confidence']}%", 'Score': s['score'], 'RSI': s['rsi'],
            'Regime': s['regime'], 'Timestamp': s['timestamp']
        } for s in signals]
        st.dataframe(pd.DataFrame(df_data), use_container_width=True, height=400)

    def display_trades_table(self, trades):
        df_data = [{
            'Symbol': t['symbol'], 'Side': t['side'],
            'Entry': f"${t['entry']}", 'Exit': f"${t['exit']}", 'Quantity': t['qty'],
            'P&L': f"{'🟢' if t['pnl'] > 0 else '🔴'} ${t['pnl']}",
            'Strategy': t['strategy'], 'Timestamp': t['timestamp']
        } for t in trades]
        st.dataframe(pd.DataFrame(df_data), use_container_width=True, height=400)

    def display_trade_statistics(self, stats):
        st.metric("Total Trades", stats.get('total_trades', 0))
        st.metric("Win Rate", f"{stats.get('win_rate', 0)}%")
        st.metric("Total P&L", f"${format_currency(stats.get('total_pnl', 0))}")
        st.metric("Avg Win", f"${format_currency(stats.get('avg_win', 0))}")
        st.metric("Avg Loss", f"${format_currency(stats.get('avg_loss', 0))}")
        st.metric("Profit Factor", stats.get('profit_factor', 0))

    def create_portfolio_performance_chart(self, trades, current_balance):
        if not trades:
            return go.Figure()

        dates, cumulative_pnl, running_total = [], [], 10.0
        for t in trades:
            running_total += t['pnl']
            cumulative_pnl.append(running_total)
            try:
                dt = datetime.fromisoformat(t['timestamp'])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dates.append(dt)
            except:
                dates.append(datetime.now(timezone.utc))

        fig = go.Figure(go.Scatter(x=dates, y=cumulative_pnl, mode='lines+markers',
                                   line=dict(color='#00d4aa', width=2)))
        fig.update_layout(title="Portfolio Performance Over Time",
                          xaxis_title="Date", yaxis_title="Portfolio Value ($)",
                          height=400, template="plotly_dark")
        return fig

    def create_detailed_performance_chart(self, trades, current_balance):
        if not trades:
            return go.Figure()

        cumulative_pnl, daily_pnl, dates = [], [], []
        running_total = 10.0

        for t in trades:
            running_total += t['pnl']
            cumulative_pnl.append(running_total)
            daily_pnl.append(t['pnl'])
            try:
                dt = datetime.fromisoformat(t['timestamp'])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dates.append(dt)
            except:
                dates.append(datetime.now(timezone.utc))

        fig = make_subplots(rows=2, cols=1,
                            subplot_titles=('Portfolio Value', 'Daily P&L'),
                            row_heights=[0.7, 0.3], vertical_spacing=0.1)

        fig.add_trace(go.Scatter(x=dates, y=cumulative_pnl, mode='lines+markers',
                                 line=dict(color='#00d4aa', width=2)), row=1, col=1)

        bar_colors = ['green' if x > 0 else 'red' for x in daily_pnl]
        fig.add_trace(go.Bar(x=dates, y=daily_pnl, marker_color=bar_colors), row=2, col=1)

        fig.update_layout(height=600, template="plotly_dark", showlegend=False)
        return fig

    def create_technical_chart(self, chart_data, symbol, indicators):
        if not chart_data:
            return go.Figure()

        df = pd.DataFrame(chart_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        fig = make_subplots(rows=3, cols=1,
                            subplot_titles=(f'{symbol} Price Chart', 'Volume', 'RSI'),
                            row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.05)

        fig.add_trace(go.Candlestick(
            x=df['timestamp'], open=df['open'], high=df['high'],
            low=df['low'], close=df['close'], name=symbol), row=1, col=1)

        close_prices = df['close'].tolist()

        if 'EMA 9' in indicators:
            ema9 = self.engine.ema(close_prices, 9)
            fig.add_trace(go.Scatter(x=df['timestamp'], y=ema9, mode='lines',
                                     name='EMA 9', line=dict(color='orange', width=1)), row=1, col=1)

        if 'EMA 21' in indicators:
            ema21 = self.engine.ema(close_prices, 21)
            fig.add_trace(go.Scatter(x=df['timestamp'], y=ema21, mode='lines',
                                     name='EMA 21', line=dict(color='blue', width=1)), row=1, col=1)

        if 'Bollinger Bands' in indicators:
            upper, middle, lower = zip(*self.engine.calculate_bollinger_bands(close_prices))
            fig.add_trace(go.Scatter(x=df['timestamp'], y=upper, name='BB Upper',
                                     line=dict(color='gray', width=1, dash='dash')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['timestamp'], y=lower, name='BB Lower',
                                     line=dict(color='gray', width=1, dash='dash'),
                                     fill='tonexty', fillcolor='rgba(128,128,128,0.1)'), row=1, col=1)

        bar_colors = ['green' if c > o else 'red' for c, o in zip(df['close'], df['open'])]
        fig.add_trace(go.Bar(x=df['timestamp'], y=df['volume'], marker_color=bar_colors, name='Volume'), row=2, col=1)

        if 'RSI' in indicators:
            rsi = self.engine.compute_rsi(close_prices)

        if isinstance(rsi, (list, np.ndarray, pd.Series)):
            fig.add_trace(go.Scatter(x=df['timestamp'][-len(rsi):], y=rsi, name='RSI',
                                    line=dict(color='purple', width=2)), row=3, col=1)

            fig.add_shape(type="line", x0=df['timestamp'].min(), x1=df['timestamp'].max(),
                        y0=70, y1=70, line=dict(color="red", dash="dash"), row=3, col=1)
            fig.add_shape(type="line", x0=df['timestamp'].min(), x1=df['timestamp'].max(),
                        y0=30, y1=30, line=dict(color="green", dash="dash"), row=3, col=1)

