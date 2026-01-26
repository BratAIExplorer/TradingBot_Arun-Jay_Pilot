"""
Notification System - Email & Telegram Alerts
Send real-time notifications for trading events

Part of Phase 0A - Enhanced Monitoring
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from typing import Dict, Any, Optional
from datetime import datetime


class NotificationManager:
    """Manages email and Telegram notifications"""
    
    def __init__(self, settings: Optional[Dict] = None):
        """
        Initialize notification manager
        
        Args:
            settings: Settings dictionary or SettingsManager instance
        """
        self.settings = settings or {}
        
        # Default initialization (if settings is plain dict)
        self.email_enabled = self.settings.get('notifications', {}).get('email', {}).get('enabled', False)
        self.telegram_enabled = self.settings.get('notifications', {}).get('enabled', False)
        
        # Email config
        self.smtp_server = self.settings.get('notifications', {}).get('email', {}).get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = self.settings.get('notifications', {}).get('email', {}).get('smtp_port', 587)
        self.sender_email = self.settings.get('notifications', {}).get('email', {}).get('sender_email', '')
        self.sender_password = self.settings.get('notifications', {}).get('email', {}).get('sender_password', '')
        self.recipient_email = self.settings.get('notifications', {}).get('email', {}).get('recipient_email', '')
        
        # Telegram config
        self.telegram_token = self.settings.get('notifications', {}).get('telegram_bot_token', '')
        self.telegram_chat_id = self.settings.get('notifications', {}).get('telegram_chat_id', '')
        
        # If settings is a SettingsManager instance, use its decryption
        from settings_manager import SettingsManager
        if isinstance(self.settings, SettingsManager):
            self._mgr = self.settings
            self.telegram_enabled = self._mgr.get('notifications.enabled', False)
            self.telegram_token = self._mgr.get_decrypted('notifications.telegram_bot_token', '')
            self.telegram_chat_id = self._mgr.get('notifications.telegram_chat_id', '')
            
            self.email_enabled = self._mgr.get('notifications.email.enabled', False)
            self.sender_email = self._mgr.get('notifications.email.sender_email', '')
            self.sender_password = self._mgr.get_decrypted('notifications.email.sender_password', '')
            self.recipient_email = self._mgr.get('notifications.email.recipient_email', '')
    
    def send_trade_alert(self, trade_data: Dict[str, Any]):
        """Send notification when trade is executed"""
        if self.email_enabled:
            self._send_email_trade(trade_data)
        
        if self.telegram_enabled:
            self._send_telegram_trade(trade_data)
    
    def send_stop_loss_alert(self, position: Dict[str, Any]):
        """Send notification when stop-loss is hit"""
        if self.email_enabled:
            self._send_email_stop_loss(position)
        
        if self.telegram_enabled:
            self._send_telegram_stop_loss(position)
    
    def send_profit_target_alert(self, position: Dict[str, Any]):
        """Send notification when profit target is hit"""
        if self.email_enabled:
            self._send_email_profit_target(position)
        
        if self.telegram_enabled:
            self._send_telegram_profit_target(position)
    
    def send_auth_alert(self, details: Dict[str, Any] = None):
        """Send notification when authentication (token refresh) is required"""
        if self.email_enabled:
            self._send_email_auth(details)
        
        if self.telegram_enabled:
            self._send_telegram_auth(details)

    def send_circuit_breaker_alert(self, details: Dict[str, Any]):
        """Send notification when circuit breaker is triggered"""
        if self.email_enabled:
            self._send_email_circuit_breaker(details)
        
        if self.telegram_enabled:
            self._send_telegram_circuit_breaker(details)

    def send_heartbeat(self, details: Dict[str, Any]):
        """Send periodic status update to Telegram"""
        if not self.telegram_enabled: return
        
        status = details.get('status', 'RUNNING')
        pnl = details.get('total_pnl', 0)
        positions = details.get('positions_count', 0)
        
        heart_emoji = "💙" if status == "RUNNING" else "⏳"
        
        message = f"""
{heart_emoji} <b>ARUN HEARTBEAT</b>
Status: {status}
Positions: {positions}
Total P&L: ₹{pnl:,.2f}
Time: {datetime.now().strftime('%H:%M')}
        """
        self._send_telegram(message)

    def send_sos(self, error_msg: str):
        """Send emergency alert if engine crashes"""
        if not self.telegram_enabled: return
        
        message = f"""
🚨 <b>ARUN ENGINE ALERT (SOS)</b>
The trading engine has encountered a critical error or manual stop.

<b>Error:</b> {error_msg}
<b>Action:</b> Trading Suspended.

Please check the Desktop GUI for details.
        """
        self._send_telegram(message)
        """Send email notification for trade"""
        if not self.sender_email or not self.sender_password:
            return
        
        action_emoji = "🟢" if trade['action'] == "BUY" else "🔴"
        subject = f"{action_emoji} ARUN Bot - {trade['action']} {trade['symbol']}"
        
        body = f"""
TRADE EXECUTED:
Symbol: {trade['symbol']} ({trade['exchange']})
Action: {trade['action']}
Quantity: {trade['quantity']} shares
Price: ₹{trade['price']:,.2f}

FINANCIALS:
Gross Amount: ₹{trade.get('gross_amount', 0):,.2f}
Total Fees: ₹{trade.get('total_fees', 0):.2f}
Net Amount: ₹{trade.get('net_amount', 0):,.2f}

STRATEGY:
Strategy: {trade.get('strategy', 'N/A')}
Reason: {trade.get('reason', 'N/A')}

TIMESTAMP: {trade.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}

---
ARUN Trading Bot
        """
        
        self._send_email(subject, body)
    
    def _send_email_stop_loss(self, position: Dict[str, Any]):
        """Send email notification for stop-loss hit"""
        subject = f"🛑 STOP-LOSS HIT - {position['symbol']}"
        
        body = f"""
STOP-LOSS TRIGGERED:
Symbol: {position['symbol']}
Entry Price: ₹{position.get('entry_price', 0):,.2f}
Current Price: ₹{position.get('current_price', 0):,.2f}
Loss: ₹{position.get('loss_amount', 0):,.2f} ({position.get('loss_pct', 0):.2f}%)

Position automatically closed to protect capital.

TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
ARUN Trading Bot
        """
        
        self._send_email(subject, body)
    
    def _send_email_profit_target(self, position: Dict[str, Any]):
        """Send email notification for profit target hit"""
        subject = f"🎯 PROFIT TARGET HIT - {position['symbol']}"
        
        body = f"""
PROFIT TARGET ACHIEVED:
Symbol: {position['symbol']}
Entry Price: ₹{position.get('entry_price', 0):,.2f}
Exit Price: ₹{position.get('exit_price', 0):,.2f}
Net Profit: ₹{position.get('profit_amount', 0):,.2f} (+{position.get('profit_pct', 0):.2f}%)

Congratulations! Position closed at target.

TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
ARUN Trading Bot
        """
        
        self._send_email(subject, body)
    
    def _send_email_auth(self, details: Dict[str, Any] = None):
        """Send email notification for authentication required"""
        subject = "🔑 ACTION REQUIRED: ARUN Bot Token Refresh"
        
        body = f"""
AUTHENTICATION REQUIRED:
The mStock API session has expired or is missing. 

Please open the ARUN Trading Bot and follow the prompts to:
1. Refresh your session
2. Enter the OTP sent to your registered device

TRADING IS PAUSED until this is completed.

TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
ARUN Trading Bot
        """
        self._send_email(subject, body)

    def _send_email_circuit_breaker(self, details: Dict[str, Any]):
        """Send email notification for circuit breaker"""
        subject = "🚨 CIRCUIT BREAKER ACTIVATED - Trading Halted"
        
        body = f"""
CIRCUIT BREAKER TRIGGERED:

Daily Loss Limit Reached: {details.get('loss_pct', 0):.2f}%
Portfolio Value: ₹{details.get('portfolio_value', 0):,.2f}
Daily Loss: ₹{details.get('daily_loss', 0):,.2f}

TRADING HAS BEEN HALTED FOR THE DAY.
Bot will resume tomorrow.

Review your strategy and risk settings before continuing.

TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
ARUN Trading Bot
        """
        
        self._send_email(subject, body)
    
    def _send_email(self, subject: str, body: str):
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent: {subject}")
        except Exception as e:
            print(f"❌ Email failed: {e}")
    
    def _send_telegram_trade(self, trade: Dict[str, Any]):
        """Send Telegram notification for trade"""
        action_emoji = "🟢" if trade['action'] == "BUY" else "🔴"
        
        message = f"""
{action_emoji} <b>{trade['action']}: {trade['symbol']}</b>

Price: ₹{trade['price']:,.2f}
Quantity: {trade['quantity']}
Net: ₹{trade.get('net_amount', 0):,.2f}

Strategy: {trade.get('strategy', 'N/A')}
Time: {trade.get('timestamp', datetime.now().strftime('%H:%M:%S'))}
        """
        
        self._send_telegram(message)
    
    def _send_telegram_stop_loss(self, position: Dict[str, Any]):
        """Send Telegram notification for stop-loss"""
        message = f"""
🛑 <b>STOP-LOSS HIT</b>

Symbol: {position['symbol']}
Loss: ₹{position.get('loss_amount', 0):,.2f} ({position.get('loss_pct', 0):.2f}%)

Position closed automatically.
        """
        
        self._send_telegram(message)
    
    def _send_telegram_profit_target(self, position: Dict[str, Any]):
        """Send Telegram notification for profit target"""
        message = f"""
🎯 <b>PROFIT TARGET HIT!</b>

Symbol: {position['symbol']}
Profit: ₹{position.get('profit_amount', 0):,.2f} (+{position.get('profit_pct', 0):.2f}%)

Great job! Position closed at target.
        """
        
        self._send_telegram(message)
    
    def _send_telegram_auth(self, details: Dict[str, Any] = None):
        """Send Telegram notification for authentication required"""
        message = f"""
🔑 <b>ACTION REQUIRED: TOKEN REFRESH</b>

Your mStock session has expired. 

Please check your registered phone for an OTP and enter it in the bot window to resume trading.

<b>Bot is currently PAUSED.</b>
        """
        self._send_telegram(message)

    def _send_telegram_circuit_breaker(self, details: Dict[str, Any]):
        """Send Telegram notification for circuit breaker"""
        message = f"""
🚨 <b>CIRCUIT BREAKER ACTIVATED</b>

Daily loss limit reached: {details.get('loss_pct', 0):.2f}%
Portfolio: ₹{details.get('portfolio_value', 0):,.2f}

<b>Trading halted for the day.</b>
        """
        
        self._send_telegram(message)
    
    def _send_telegram(self, message: str):
        """Send message via Telegram Bot API"""
        if not self.telegram_token or not self.telegram_chat_id:
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Telegram sent")
            else:
                print(f"❌ Telegram failed: {response.text}")
        except Exception as e:
            print(f"❌ Telegram error: {e}")
    
    def test_email(self) -> bool:
        """Test email configuration"""
        try:
            self._send_email(
                "ARUN Bot - Test Email",
                "This is a test email from ARUN Trading Bot.\n\nIf you received this, email notifications are working correctly!"
            )
            return True
        except Exception as e:
            print(f"❌ Email test failed: {e}")
            return False
    
    def test_telegram(self) -> bool:
        """Test Telegram configuration"""
        try:
            self._send_telegram("<b>ARUN Bot - Test Message</b>\n\nIf you received this, Telegram notifications are working correctly!")
            return True
        except Exception as e:
            print(f"❌ Telegram test failed: {e}")
            return False


# Convenience function for quick notifications
def notify_trade(trade_data: Dict, settings: Dict):
    """Send trade notification"""
    notifier = NotificationManager(settings)
    notifier.send_trade_alert(trade_data)


def notify_stop_loss(position: Dict, settings: Dict):
    """Send stop-loss notification"""
    notifier = NotificationManager(settings)
    notifier.send_stop_loss_alert(position)


def notify_profit_target(position: Dict, settings: Dict):
    """Send profit target notification"""
    notifier = NotificationManager(settings)
    notifier.send_profit_target_alert(position)


def notify_auth(settings: Dict, details: Dict = None):
    """Send authentication alert"""
    notifier = NotificationManager(settings)
    notifier.send_auth_alert(details)


def notify_circuit_breaker(details: Dict, settings: Dict):
    """Send circuit breaker notification"""
    notifier = NotificationManager(settings)
    notifier.send_circuit_breaker_alert(details)


if __name__ == "__main__":
    # Test notification system
    print("🧪 Testing Notification System...\n")
    
    # Mock settings (replace with real credentials to test)
    mock_settings = {
        'notifications': {
            'email': {
                'enabled': False,  # Set to True and add credentials to test
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender_email': 'your_email@gmail.com',
                'sender_password': 'your_app_password',
                'recipient_email': 'your_email@gmail.com'
            },
            'telegram': {
                'enabled': False,  # Set to True and add credentials to test
                'bot_token': 'YOUR_BOT_TOKEN',
                'chat_id': 'YOUR_CHAT_ID'
            }
        }
    }
    
    notifier = NotificationManager(mock_settings)
    
    # Mock trade data
    mock_trade = {
        'symbol': 'MICEL',
        'exchange': 'BSE',
        'action': 'BUY',
        'quantity': 10,
        'price': 245.50,
        'gross_amount': 2455.00,
        'total_fees': 26.51,
        'net_amount': 2481.51,
        'strategy': 'RSI',
        'reason': 'RSI below 35',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    print("📧 Email Enabled:", notifier.email_enabled)
    print("📱 Telegram Enabled:", notifier.telegram_enabled)
    
    if notifier.email_enabled:
        print("\n✉️ Testing email...")
        notifier.test_email()
    
    if notifier.telegram_enabled:
        print("\n📲 Testing Telegram...")
        notifier.test_telegram()
    
    print("\n✅ Notification system ready (configure credentials in settings.json to enable)")
