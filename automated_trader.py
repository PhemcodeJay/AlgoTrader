import time
import json
import os
from datetime import datetime, timedelta
import threading
from trading_engine import TradingEngine
from data_provider import DataProvider
from database import db_manager
import logging

class AutomatedTrader:
    def __init__(self):
        self.trading_engine = TradingEngine()
        self.data_provider = DataProvider()
        self.is_running = False
        self.automation_thread = None
        
        # Automation settings
        self.signal_generation_interval = 300  # 5 minutes
        self.trade_execution_enabled = True
        self.min_confidence_threshold = 75
        self.max_signals_per_cycle = 5
        self.max_daily_trades = 20
        
        # Risk management
        self.max_position_size_pct = 5  # 5% of portfolio per trade
        self.max_drawdown_limit = 20   # Stop trading if drawdown exceeds 20%
        
        # Logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('automated_trader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # State tracking
        self.daily_trades_count = 0
        self.last_signal_generation = None
        self.automation_stats = db_manager.get_automation_stats()
    
    def load_automation_settings(self):
        """Load automation settings from database"""
        try:
            settings = db_manager.get_setting('automation_settings', {})
            self.signal_generation_interval = settings.get('signal_interval', 300)
            self.trade_execution_enabled = settings.get('trade_execution', True)
            self.min_confidence_threshold = settings.get('min_confidence', 75)
            self.max_signals_per_cycle = settings.get('max_signals', 5)
            self.max_daily_trades = settings.get('max_daily_trades', 20)
            self.max_position_size_pct = settings.get('max_position_size', 5)
            self.max_drawdown_limit = settings.get('max_drawdown', 20)
            self.logger.info("Automation settings loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading automation settings: {e}")
    
    def save_automation_settings(self):
        """Save automation settings to database"""
        settings = {
            'signal_interval': self.signal_generation_interval,
            'trade_execution': self.trade_execution_enabled,
            'min_confidence': self.min_confidence_threshold,
            'max_signals': self.max_signals_per_cycle,
            'max_daily_trades': self.max_daily_trades,
            'max_position_size': self.max_position_size_pct,
            'max_drawdown': self.max_drawdown_limit
        }
        
        try:
            db_manager.set_setting('automation_settings', settings, 'json')
            self.logger.info("Automation settings saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving automation settings: {e}")
    
    def check_risk_limits(self):
        """Check if trading should be paused due to risk limits"""
        # Check daily loss limit
        daily_loss_pct = self.trading_engine.today_loss_pct()
        if daily_loss_pct >= self.trading_engine.MAX_LOSS_PCT:
            self.logger.warning(f"Daily loss limit reached: {daily_loss_pct}%")
            return False
        
        # Check maximum drawdown
        trades = self.trading_engine.get_recent_trades()
        if trades:
            from utils import calculate_drawdown
            current_drawdown = calculate_drawdown(trades, self.trading_engine.START_CAPITAL)
            if current_drawdown >= self.max_drawdown_limit:
                self.logger.warning(f"Maximum drawdown limit reached: {current_drawdown}%")
                return False
        
        # Check daily trades limit
        today = datetime.utcnow().strftime("%Y-%m-%d")
        daily_trades = len([t for t in trades if t['timestamp'].startswith(today)])
        if daily_trades >= self.max_daily_trades:
            self.logger.warning(f"Daily trades limit reached: {daily_trades}")
            return False
        
        return True
    
    def generate_automated_signals(self):
        """Generate trading signals automatically"""
        try:
            if not self.check_risk_limits():
                self.logger.info("Trading paused due to risk limits")
                return []
            
            # Get popular symbols for analysis
            symbols = self.data_provider.get_popular_symbols()
            
            # Generate signals
            signals = self.trading_engine.generate_signals(
                symbol_limit=len(symbols),
                confidence_threshold=self.min_confidence_threshold
            )
            
            # Filter and rank signals
            filtered_signals = [s for s in signals if s.get('confidence', 0) >= self.min_confidence_threshold]
            filtered_signals.sort(key=lambda x: (x.get('score', 0), x.get('confidence', 0)), reverse=True)
            
            # Limit number of signals
            top_signals = filtered_signals[:self.max_signals_per_cycle]
            
            self.automation_stats['signals_generated'] += len(top_signals)
            self.automation_stats['last_update'] = datetime.now().isoformat()
            
            # Save stats to database
            db_manager.update_automation_stats(self.automation_stats)
            
            self.logger.info(f"Generated {len(top_signals)} automated signals")
            return top_signals
            
        except Exception as e:
            self.logger.error(f"Error generating automated signals: {e}")
            return []
    
    def execute_automated_trade(self, signal):
        """Execute a trade automatically based on signal"""
        try:
            if not self.trade_execution_enabled:
                self.logger.info(f"Trade execution disabled for {signal['symbol']}")
                return None
            
            # Additional risk check per trade
            current_balance = self.trading_engine.load_capital()
            max_risk_amount = current_balance * (self.max_position_size_pct / 100)
            
            # Calculate position size
            risk_per_unit = abs(signal['entry'] - signal['sl'])
            if risk_per_unit <= 0:
                self.logger.warning(f"Invalid risk calculation for {signal['symbol']}")
                return None
            
            position_size = max_risk_amount / risk_per_unit
            
            # Execute trade simulation
            trade = self.trading_engine.simulate_trade(signal)
            
            if trade:
                self.automation_stats['trades_executed'] += 1
                if trade['pnl'] > 0:
                    self.automation_stats['successful_trades'] += 1
                self.automation_stats['total_pnl'] += trade['pnl']
                
                # Save stats to database
                db_manager.update_automation_stats(self.automation_stats)
                
                # Post to social media if configured
                try:
                    if self.trading_engine.DISCORD_WEBHOOK_URL:
                        self.trading_engine.post_signal_to_discord(signal)
                    self.trading_engine.post_signal_to_reddit(signal)
                except Exception as e:
                    self.logger.warning(f"Social media posting failed: {e}")
                
                self.logger.info(f"Executed automated trade: {signal['symbol']} | P&L: ${trade['pnl']}")
                return trade
            
        except Exception as e:
            self.logger.error(f"Error executing automated trade for {signal['symbol']}: {e}")
            return None
    
    def automation_cycle(self):
        """Main automation cycle"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check if it's time to generate signals
                if (self.last_signal_generation is None or 
                    (current_time - self.last_signal_generation).seconds >= self.signal_generation_interval):
                    
                    self.logger.info("Starting automated signal generation cycle")
                    
                    # Generate signals
                    signals = self.generate_automated_signals()
                    
                    # Execute trades for qualified signals
                    for signal in signals:
                        if self.check_risk_limits():
                            trade = self.execute_automated_trade(signal)
                            if trade:
                                # Small delay between trades
                                time.sleep(5)
                        else:
                            self.logger.info("Risk limits reached, stopping trade execution")
                            break
                    
                    self.last_signal_generation = current_time
                    self.logger.info(f"Automation cycle completed. Next cycle in {self.signal_generation_interval} seconds")
                
                # Sleep for a short interval before checking again
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in automation cycle: {e}")
                time.sleep(60)  # Wait longer on error
    
    def start_automation(self):
        """Start the automated trading"""
        if self.is_running:
            self.logger.warning("Automation is already running")
            return False
        
        self.load_automation_settings()
        self.is_running = True
        self.automation_stats['start_time'] = datetime.now().isoformat()
        
        # Start automation in a separate thread
        self.automation_thread = threading.Thread(target=self.automation_cycle, daemon=True)
        self.automation_thread.start()
        
        self.logger.info("Automated trading started")
        return True
    
    def stop_automation(self):
        """Stop the automated trading"""
        if not self.is_running:
            self.logger.warning("Automation is not running")
            return False
        
        self.is_running = False
        
        if self.automation_thread and self.automation_thread.is_alive():
            self.automation_thread.join(timeout=10)
        
        self.logger.info("Automated trading stopped")
        return True
    
    def get_automation_status(self):
        """Get current automation status and statistics"""
        return {
            'is_running': self.is_running,
            'settings': {
                'signal_interval': self.signal_generation_interval,
                'trade_execution': self.trade_execution_enabled,
                'min_confidence': self.min_confidence_threshold,
                'max_signals_per_cycle': self.max_signals_per_cycle,
                'max_daily_trades': self.max_daily_trades,
                'max_position_size_pct': self.max_position_size_pct,
                'max_drawdown_limit': self.max_drawdown_limit
            },
            'stats': self.automation_stats,
            'last_signal_generation': self.last_signal_generation.isoformat() if self.last_signal_generation else None,
            'next_signal_generation': (
                self.last_signal_generation + timedelta(seconds=self.signal_generation_interval)
            ).isoformat() if self.last_signal_generation else None
        }
    
    def update_settings(self, new_settings):
        """Update automation settings"""
        try:
            if 'signal_interval' in new_settings:
                self.signal_generation_interval = max(60, int(new_settings['signal_interval']))
            
            if 'trade_execution' in new_settings:
                self.trade_execution_enabled = bool(new_settings['trade_execution'])
            
            if 'min_confidence' in new_settings:
                self.min_confidence_threshold = max(50, min(95, int(new_settings['min_confidence'])))
            
            if 'max_signals' in new_settings:
                self.max_signals_per_cycle = max(1, min(10, int(new_settings['max_signals'])))
            
            if 'max_daily_trades' in new_settings:
                self.max_daily_trades = max(1, min(100, int(new_settings['max_daily_trades'])))
            
            if 'max_position_size' in new_settings:
                self.max_position_size_pct = max(0.5, min(20, float(new_settings['max_position_size'])))
            
            if 'max_drawdown' in new_settings:
                self.max_drawdown_limit = max(5, min(50, float(new_settings['max_drawdown'])))
            
            self.save_automation_settings()
            self.logger.info("Automation settings updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating automation settings: {e}")
            return False

# Global instance for the automation system
automated_trader = AutomatedTrader()