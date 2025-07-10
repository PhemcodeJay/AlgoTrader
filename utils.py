def format_currency(value, decimals=2):
    """Format currency value with appropriate decimal places"""
    if value is None:
        return "0.00"
    
    try:
        if abs(value) >= 1000000:
            return f"{value/1000000:.1f}M"
        elif abs(value) >= 1000:
            return f"{value/1000:.1f}K"
        else:
            return f"{value:.{decimals}f}"
    except (TypeError, ValueError):
        return "0.00"

def format_percentage(value, decimals=2):
    """Format percentage value"""
    if value is None:
        return "0.00"
    
    try:
        return f"{value:.{decimals}f}"
    except (TypeError, ValueError):
        return "0.00"

def get_status_color(daily_pnl_pct):
    """Get color based on P&L percentage"""
    if daily_pnl_pct > 5:
        return "#00ff00"  # Bright green
    elif daily_pnl_pct > 0:
        return "#90EE90"  # Light green
    elif daily_pnl_pct > -5:
        return "#FFD700"  # Gold/yellow
    elif daily_pnl_pct > -10:
        return "#FFA500"  # Orange
    else:
        return "#FF0000"  # Red

def get_trend_color(change_pct):
    """Get color for trend indication"""
    if change_pct > 0:
        return "#00d4aa"  # Green
    elif change_pct < 0:
        return "#ff4444"  # Red
    else:
        return "#888888"  # Gray

def calculate_risk_reward_ratio(entry, tp, sl):
    """Calculate risk-reward ratio"""
    try:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        return reward / risk if risk > 0 else 0
    except (TypeError, ZeroDivisionError):
        return 0

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    try:
        from datetime import datetime
        # Handle different timestamp formats
        if 'UTC' in timestamp_str:
            dt = datetime.strptime(timestamp_str.split(' UTC')[0], "%Y-%m-%d %H:%M")
        else:
            dt = datetime.strptime(timestamp_str.split()[0], "%Y-%m-%d")
        
        return dt.strftime("%m/%d %H:%M")
    except:
        return timestamp_str

def validate_trading_parameters(tp_pct, sl_pct, leverage):
    """Validate trading parameters"""
    errors = []
    
    if tp_pct <= 0:
        errors.append("Take profit percentage must be positive")
    
    if sl_pct <= 0:
        errors.append("Stop loss percentage must be positive")
    
    if leverage < 1 or leverage > 50:
        errors.append("Leverage must be between 1 and 50")
    
    if tp_pct <= sl_pct:
        errors.append("Take profit should be greater than stop loss")
    
    return errors

def calculate_position_size(capital, risk_pct, entry_price, sl_price):
    """Calculate position size based on risk management"""
    try:
        risk_amount = capital * (risk_pct / 100)
        risk_per_unit = abs(entry_price - sl_price)
        
        if risk_per_unit <= 0:
            return 0
        
        position_size = risk_amount / risk_per_unit
        return round(position_size, 6)
    
    except (TypeError, ZeroDivisionError):
        return 0

def get_signal_strength_text(confidence):
    """Get signal strength description"""
    if confidence >= 90:
        return "🔥 Very Strong"
    elif confidence >= 85:
        return "💪 Strong"
    elif confidence >= 75:
        return "👍 Good"
    elif confidence >= 65:
        return "⚠️ Weak"
    else:
        return "❌ Very Weak"

def calculate_drawdown(trades, starting_capital):
    """Calculate maximum drawdown from trades"""
    if not trades:
        return 0
    
    peak = starting_capital
    max_drawdown = 0
    current_capital = starting_capital
    
    for trade in trades:
        current_capital += trade.get('pnl', 0)
        
        if current_capital > peak:
            peak = current_capital
        
        drawdown = (peak - current_capital) / peak * 100
        max_drawdown = max(max_drawdown, drawdown)
    
    return round(max_drawdown, 2)