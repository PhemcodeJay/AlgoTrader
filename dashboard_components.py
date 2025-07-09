import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from utils import format_currency, format_percentage, get_trend_color

class DashboardComponents:
    def __init__(self):
        pass
    
    def display_signal_card(self, signal):
        """Display a signal card with key information"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**{signal['symbol']}** - {signal['side']}")
            st.markdown(f"Strategy: {signal['strategy']}")
            st.markdown(f"Entry: ${signal['entry']}")
            st.markdown(f"TP: ${signal['tp']} | SL: ${signal['sl']}")
            
        with col2:
            # Confidence badge
            confidence_color = "green" if signal['confidence'] >= 85 else "orange" if signal['confidence'] >= 75 else "red"
            st.markdown(f"<div style='background-color: {confidence_color}; color: white; padding: 5px; border-radius: 5px; text-align: center;'>{signal['confidence']}% Confidence</div>", unsafe_allow_html=True)
            st.markdown(f"Score: {signal['score']}")
            st.markdown(f"RSI: {signal['rsi']}")
    
    def display_signals_table(self, signals):
        """Display signals in a table format"""
        df_data = []
        for signal in signals:
            df_data.append({
                'Symbol': signal['symbol'],
                'Side': signal['side'],
                'Strategy': signal['strategy'],
                'Entry': f"${signal['entry']}",
                'TP': f"${signal['tp']}",
                'SL': f"${signal['sl']}",
                'Confidence': f"{signal['confidence']}%",
                'Score': signal['score'],
                'RSI': signal['rsi'],
                'Regime': signal['regime'],
                'Timestamp': signal['timestamp']
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, height=400)
    
    def display_trades_table(self, trades):
        """Display trades in a table format"""
        df_data = []
        for trade in trades:
            pnl_color = "🟢" if trade['pnl'] > 0 else "🔴"
            df_data.append({
                'Symbol': trade['symbol'],
                'Side': trade['side'],
                'Entry': f"${trade['entry']}",
                'Exit': f"${trade['exit']}",
                'Quantity': trade['qty'],
                'P&L': f"{pnl_color} ${trade['pnl']}",
                'Strategy': trade['strategy'],
                'Timestamp': trade['timestamp']
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, height=400)
    
    def display_trade_statistics(self, stats):
        """Display trade statistics"""
        st.metric("Total Trades", stats.get('total_trades', 0))
        st.metric("Win Rate", f"{stats.get('win_rate', 0)}%")
        st.metric("Total P&L", f"${format_currency(stats.get('total_pnl', 0))}")
        st.metric("Avg Win", f"${format_currency(stats.get('avg_win', 0))}")
        st.metric("Avg Loss", f"${format_currency(stats.get('avg_loss', 0))}")
        st.metric("Profit Factor", stats.get('profit_factor', 0))
    
    def create_portfolio_performance_chart(self, trades, current_balance):
        """Create portfolio performance chart"""
        if not trades:
            return go.Figure()
        
        # Calculate cumulative performance
        cumulative_pnl = []
        running_total = 10.0  # Starting capital
        dates = []
        
        for trade in trades:
            running_total += trade['pnl']
            cumulative_pnl.append(running_total)
            # Parse timestamp
            try:
                date = datetime.strptime(trade['timestamp'].split()[0], "%Y-%m-%d")
                dates.append(date)
            except:
                dates.append(datetime.now())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=cumulative_pnl,
            mode='lines+markers',
            name='Portfolio Value',
            line=dict(color='#00d4aa', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Portfolio Performance Over Time",
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            height=400,
            template="plotly_dark"
        )
        
        return fig
    
    def create_detailed_performance_chart(self, trades, current_balance):
        """Create detailed performance chart with multiple metrics"""
        if not trades:
            return go.Figure()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Portfolio Value', 'Daily P&L'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Portfolio value over time
        cumulative_pnl = []
        daily_pnl = []
        running_total = 10.0
        dates = []
        
        for trade in trades:
            running_total += trade['pnl']
            cumulative_pnl.append(running_total)
            daily_pnl.append(trade['pnl'])
            try:
                date = datetime.strptime(trade['timestamp'].split()[0], "%Y-%m-%d")
                dates.append(date)
            except:
                dates.append(datetime.now())
        
        # Portfolio value line
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=cumulative_pnl,
                mode='lines+markers',
                name='Portfolio Value',
                line=dict(color='#00d4aa', width=2)
            ),
            row=1, col=1
        )
        
        # Daily P&L bars
        colors = ['green' if pnl > 0 else 'red' for pnl in daily_pnl]
        fig.add_trace(
            go.Bar(
                x=dates,
                y=daily_pnl,
                name='Daily P&L',
                marker_color=colors
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=600,
            template="plotly_dark",
            showlegend=True
        )
        
        return fig
    
    def create_technical_chart(self, chart_data, symbol, indicators):
        """Create technical analysis chart"""
        if not chart_data:
            return go.Figure()
        
        df = pd.DataFrame(chart_data, columns=['high', 'low', 'close', 'volume', 'open'])
        df['timestamp'] = pd.date_range(start=datetime.now() - timedelta(hours=len(df)), periods=len(df), freq='H')
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=(f'{symbol} Price Chart', 'Volume', 'RSI'),
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=symbol
            ),
            row=1, col=1
        )
        
        # Add technical indicators
        if 'EMA 9' in indicators:
            from trading_engine import TradingEngine
            engine = TradingEngine()
            ema9 = engine.ema(df['close'].tolist(), 9)
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=ema9,
                    mode='lines',
                    name='EMA 9',
                    line=dict(color='orange', width=1)
                ),
                row=1, col=1
            )
        
        if 'EMA 21' in indicators:
            from trading_engine import TradingEngine
            engine = TradingEngine()
            ema21 = engine.ema(df['close'].tolist(), 21)
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=ema21,
                    mode='lines',
                    name='EMA 21',
                    line=dict(color='blue', width=1)
                ),
                row=1, col=1
            )
        
        if 'Bollinger Bands' in indicators:
            from trading_engine import TradingEngine
            engine = TradingEngine()
            bb_bands = engine.calculate_bollinger_bands(df['close'].tolist())
            bb_upper, bb_mid, bb_lower = zip(*bb_bands)
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=bb_upper,
                    mode='lines',
                    name='BB Upper',
                    line=dict(color='gray', width=1, dash='dash')
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=bb_lower,
                    mode='lines',
                    name='BB Lower',
                    line=dict(color='gray', width=1, dash='dash'),
                    fill='tonexty',
                    fillcolor='rgba(128,128,128,0.1)'
                ),
                row=1, col=1
            )
        
        # Volume chart
        colors = ['green' if df.iloc[i]['close'] > df.iloc[i]['open'] else 'red' for i in range(len(df))]
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['volume'],
                name='Volume',
                marker_color=colors
            ),
            row=2, col=1
        )
        
        # RSI
        if 'RSI' in indicators:
            from trading_engine import TradingEngine
            engine = TradingEngine()
            rsi_values = [engine.compute_rsi(df['close'].tolist()[:i+14]) for i in range(14, len(df))]
            rsi_timestamps = df['timestamp'][14:]
            
            fig.add_trace(
                go.Scatter(
                    x=rsi_timestamps,
                    y=rsi_values,
                    mode='lines',
                    name='RSI',
                    line=dict(color='purple', width=2)
                ),
                row=3, col=1
            )
            
            # Add RSI levels
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        
        fig.update_layout(
            height=800,
            template="plotly_dark",
            xaxis_rangeslider_visible=False
        )
        
        return fig
    
    def display_market_overview(self, market_data):
        """Display market overview with key metrics"""
        col1, col2, col3, col4 = st.columns(4)

        for i, data in enumerate(market_data):
            symbol = data.get('symbol', 'N/A')
            col = [col1, col2, col3, col4][i % 4]

            with col:
                price_change = data.get('price_change_pct', 0)
                color = get_trend_color(price_change)

                st.markdown(f"""
                <div style='border: 1px solid #444; border-radius: 10px; padding: 10px; margin: 5px;'>
                    <h4 style='margin: 0; color: white;'>{symbol}</h4>
                    <p style='margin: 5px 0; font-size: 20px; color: white;'>${data.get('price', 'N/A')}</p>
                    <p style='margin: 0; color: {color};'>{format_percentage(price_change)}%</p>
                </div>
                """, unsafe_allow_html=True)
