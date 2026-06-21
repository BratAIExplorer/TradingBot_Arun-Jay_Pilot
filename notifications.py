"""
Notification System - Email & Telegram Alerts + Alert Database Storage
ARUN Trading Bot v2.6.0 - Alert System

Manages:
- Email & Telegram notifications (legacy)
- Alert database persistence with deduplication
- Severity-based routing (INFO → DB only, WARN/CRITICAL → DB + Email)
- 10-second duplicate protection within same day
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from typing import Dict, Any, Optional
from datetime import datetime

# Logger for notifications
log = logging.getLogger(__name__)


def send_email(subject: str, body: str, smtp_config: Optional[Dict] = None) -> bool:
    """
    Send email notification.

    Args:
        subject: Email subject
        body: Email body
        smtp_config: SMTP configuration dict with keys:
            - smtp_server (default: smtp.gmail.com)
            - smtp_port (default: 587)
            - sender_email
            - sender_password
            - recipient_email

    Returns:
        True if email sent successfully, False otherwise
    """
    if not smtp_config:
        log.warning("SMTP config missing, email not sent")
        return False

    if not smtp_config.get("sender_email") or not smtp_config.get("sender_password"):
        log.warning("Email credentials missing, email not sent")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_config["sender_email"]
        msg["To"] = smtp_config.get("recipient_email", smtp_config["sender_email"])
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(
            smtp_config.get("smtp_server", "smtp.gmail.com"),
            smtp_config.get("smtp_port", 587),
        )
        server.starttls()
        server.login(smtp_config["sender_email"], smtp_config["sender_password"])
        server.send_message(msg)
        server.quit()

        log.info(f"Email sent: {subject}")
        return True
    except Exception as e:
        log.warning(f"Email delivery failed: {e}")
        return False


class NotificationManager:
    """Manages email and Telegram notifications + alert database persistence"""

    def __init__(self, settings: Optional[Dict] = None, db=None):
        """
        Initialize notification manager

        Args:
            settings: Settings dictionary or SettingsManager instance
            db: TradesDatabase instance for alert storage (optional)
        """
        self.settings = settings or {}
        self.db = db

        # Default initialization (if settings is plain dict)
        self.email_enabled = (
            self.settings.get("notifications", {}).get("email", {}).get("enabled", False)
        )
        self.telegram_enabled = (
            self.settings.get("notifications", {}).get("enabled", False)
        )

        # Email config
        self.smtp_server = (
            self.settings.get("notifications", {})
            .get("email", {})
            .get("smtp_server", "smtp.gmail.com")
        )
        self.smtp_port = (
            self.settings.get("notifications", {}).get("email", {}).get("smtp_port", 587)
        )
        self.sender_email = (
            self.settings.get("notifications", {})
            .get("email", {})
            .get("sender_email", "")
        )
        self.sender_password = (
            self.settings.get("notifications", {})
            .get("email", {})
            .get("sender_password", "")
        )
        self.recipient_email = (
            self.settings.get("notifications", {})
            .get("email", {})
            .get("recipient_email", "")
        )

        # Telegram config
        self.telegram_token = (
            self.settings.get("notifications", {}).get("telegram_bot_token", "")
        )
        self.telegram_chat_id = (
            self.settings.get("notifications", {}).get("telegram_chat_id", "")
        )

        # If settings is a SettingsManager instance, use its decryption
        try:
            from settings_manager import SettingsManager

            if isinstance(self.settings, SettingsManager):
                self._mgr = self.settings
                self.telegram_enabled = self._mgr.get("notifications.enabled", False)
                self.telegram_token = self._mgr.get_decrypted(
                    "notifications.telegram_bot_token", ""
                )
                self.telegram_chat_id = self._mgr.get("notifications.telegram_chat_id", "")

                self.email_enabled = self._mgr.get("notifications.email.enabled", False)
                self.sender_email = self._mgr.get("notifications.email.sender_email", "")
                self.sender_password = self._mgr.get_decrypted(
                    "notifications.email.sender_password", ""
                )
                self.recipient_email = self._mgr.get(
                    "notifications.email.recipient_email", ""
                )
        except ImportError:
            pass

    def send_alert(
        self,
        event_type: str,
        severity: str,
        message: str,
        symbol: Optional[str] = None,
        value: Optional[float] = None,
    ) -> bool:
        """
        Send alert to database and optionally email.

        Args:
            event_type: Type of event (e.g., TRADE_EXECUTED, STOP_LOSS_HIT)
            severity: Severity level (INFO, WARN, CRITICAL)
            message: Human-readable message
            symbol: Stock symbol (optional)
            value: Numeric value for deduplication (optional)

        Returns:
            True if alert was inserted (not duplicate), False if ignored
        """
        if not self.db:
            log.warning("Database not available, alert not stored")
            return False

        # Generate dedup key: event_type:symbol:rounded_value
        dedup_parts = [event_type]
        if symbol:
            dedup_parts.append(symbol)
        if value is not None:
            dedup_parts.append(str(round(value, 2)))
        dedup_key = ":".join(dedup_parts)

        # Try to insert alert with dedup protection
        try:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now().isoformat(),
                    event_type,
                    severity,
                    symbol,
                    message,
                    dedup_key,
                ),
            )
            self.db.conn.commit()

            inserted = cursor.rowcount == 1
            cursor.close()

            # Send email only if:
            # 1. Alert was inserted (not duplicate)
            # 2. Severity is WARN or CRITICAL
            if inserted and severity in ["WARN", "CRITICAL"]:
                self._send_alert_email(event_type, severity, message, symbol)

            return inserted
        except Exception as e:
            log.error(f"Failed to insert alert: {e}")
            return False

    def _send_alert_email(
        self,
        event_type: str,
        severity: str,
        message: str,
        symbol: Optional[str] = None,
    ) -> bool:
        """Send email for WARN/CRITICAL alerts"""
        if not self.email_enabled:
            return False

        severity_emoji = "⚠️" if severity == "WARN" else "🚨"
        subject = f"{severity_emoji} ARUN Alert [{severity}] - {event_type}"
        if symbol:
            subject += f" ({symbol})"

        body = f"""
ALERT NOTIFICATION:
Event: {event_type}
Severity: {severity}
Symbol: {symbol if symbol else 'N/A'}

Message:
{message}

---
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ARUN Trading Bot v2.6.0
        """

        smtp_config = {
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "sender_email": self.sender_email,
            "sender_password": self.sender_password,
            "recipient_email": self.recipient_email,
        }

        return send_email(subject, body, smtp_config)

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
        if not self.telegram_enabled:
            return

        status = details.get("status", "RUNNING")
        pnl = details.get("total_pnl", 0)
        positions = details.get("positions_count", 0)

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
        if not self.telegram_enabled:
            return

        message = f"""
🚨 <b>ARUN ENGINE ALERT (SOS)</b>
The trading engine has encountered a critical error or manual stop.

<b>Error:</b> {error_msg}
<b>Action:</b> Trading Suspended.

Please check the Desktop GUI for details.
        """
        self._send_telegram(message)

    def _send_email_trade(self, trade: Dict[str, Any]):
        """Send email notification for trade"""
        if not self.sender_email or not self.sender_password:
            return

        action_emoji = "🟢" if trade["action"] == "BUY" else "🔴"
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
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()

            log.info(f"Email sent: {subject}")
        except Exception as e:
            log.warning(f"Email failed: {e}")

    def _send_telegram_trade(self, trade: Dict[str, Any]):
        """Send Telegram notification for trade"""
        action_emoji = "🟢" if trade["action"] == "BUY" else "🔴"

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
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML",
            }

            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                log.info("Telegram sent")
            else:
                log.warning(f"Telegram failed: {response.text}")
        except Exception as e:
            log.warning(f"Telegram error: {e}")

    def test_email(self) -> bool:
        """Test email configuration"""
        try:
            self._send_email(
                "ARUN Bot - Test Email",
                "This is a test email from ARUN Trading Bot.\n\nIf you received this, email notifications are working correctly!",
            )
            return True
        except Exception as e:
            log.error(f"Email test failed: {e}")
            return False

    def test_telegram(self) -> bool:
        """Test Telegram configuration"""
        try:
            self._send_telegram(
                "<b>ARUN Bot - Test Message</b>\n\nIf you received this, Telegram notifications are working correctly!"
            )
            return True
        except Exception as e:
            log.error(f"Telegram test failed: {e}")
            return False


# Convenience functions
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
    print("Testing Notification System...\n")

    # Mock settings (replace with real credentials to test)
    mock_settings = {
        "notifications": {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your_email@gmail.com",
                "sender_password": "your_app_password",
                "recipient_email": "your_email@gmail.com",
            },
            "telegram": {
                "enabled": False,
                "bot_token": "YOUR_BOT_TOKEN",
                "chat_id": "YOUR_CHAT_ID",
            },
        }
    }

    notifier = NotificationManager(mock_settings)

    # Mock trade data
    mock_trade = {
        "symbol": "MICEL",
        "exchange": "BSE",
        "action": "BUY",
        "quantity": 10,
        "price": 245.50,
        "gross_amount": 2455.00,
        "total_fees": 26.51,
        "net_amount": 2481.51,
        "strategy": "RSI",
        "reason": "RSI below 35",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    print("Email Enabled:", notifier.email_enabled)
    print("Telegram Enabled:", notifier.telegram_enabled)

    if notifier.email_enabled:
        print("\nTesting email...")
        notifier.test_email()

    if notifier.telegram_enabled:
        print("\nTesting Telegram...")
        notifier.test_telegram()

    print("\nNotification system ready (configure credentials in settings.json to enable)")
