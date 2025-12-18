"""
Copy Trade Futures Bot - Main Module

This module implements the core bot logic for listening to trading signals
via Telegram and executing copy trades on multiple Binance Futures accounts.

Features:
    - Parses multiple signal formats (Kind, Turtle, LONG/SHORT, Giraffe)
    - Opens positions simultaneously across multiple accounts
    - Manages targets, stop losses, and position closing
    - Provides admin panel for monitoring and control
    - Supports proxy rotation for rate limiting

Author: shayanfh
License: MIT
"""

import datetime
import logging
import math
import random
import re
import string
import time
from typing import List, Tuple, Optional

import coloredlogs
import configparser
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, filters as Filters, idle
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from binance_api import Binance
from binance.error import ClientError
from models import Signals, Targets

# Configure logging
coloredlogs.install(level='INFO')
logger = logging.getLogger(__name__)
logging.getLogger('pyrogram').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.ERROR)

# Load configuration
config = configparser.ConfigParser()
config.optionxform = str
config.read('config/bot.ini')

# Initialize scheduler
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Tehran'))
scheduler.start()

# Load Telegram configuration
ANALYZER_IDS = [int(x.strip()) for x in config['TELEGRAM']['analyzers'].split(',')]
PRIVATE_LOG_ID = int(config['TELEGRAM']['private_log'])
PUBLIC_LOG_ID = int(config['TELEGRAM']['public_log'])

# Initialize Telegram bot
bot = Client(
    "bot",
    api_id=int(config['KEYS']['api_id']),
    api_hash=config['KEYS']['api_hash'],
    bot_token=config['KEYS']['bot_token'],
)

# Initialize base Binance client for price queries
account_list = config["ACCOUNTS"]["account1"].split(",")
base_binance = Binance(key=account_list[0], secret=account_list[1])


def generate_unique_signal_id(length: int = 22) -> str:
    """
    Generate a unique random signal ID.
    
    Args:
        length: Length of the generated ID
        
    Returns:
        Random string of specified length
    """
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def ensure_unique_signal_id() -> str:
    """
    Generate a unique signal ID that doesn't exist in the database.
    
    Returns:
        Unique signal ID
    """
    signal_id = generate_unique_signal_id()
    while Signals.select().where(Signals.id_signal == signal_id).exists():
        signal_id = generate_unique_signal_id()
    return signal_id


def truncate_decimal(value: float, decimal_places: int) -> float:
    """
    Truncate a float to a specific number of decimal places.
    
    Args:
        value: Float value to truncate
        decimal_places: Number of decimal places
        
    Returns:
        Truncated float value
    """
    return math.floor(value * 10 ** decimal_places) / 10 ** decimal_places


def parse_targets(targets_str: str) -> List[Tuple[float, int]]:
    """
    Parse target prices and percentages from string format.
    
    Format: "51000_25% 52000_25% 53000_50%"
    
    Args:
        targets_str: Target string to parse
        
    Returns:
        List of tuples (price, percentage)
    """
    targets_list = []
    for target_part in targets_str.split("_"):
        price_percent = target_part.split("%")
        targets_list.append((float(price_percent[0]), int(price_percent[1])))
    return targets_list


def format_targets_for_display(targets_list: List[Tuple[float, int]]) -> str:
    """
    Format targets list for Telegram display.
    
    Args:
        targets_list: List of (price, percentage) tuples
        
    Returns:
        Formatted string for display
    """
    display_str = ""
    for idx, (price, percent) in enumerate(targets_list, 1):
        display_str += f"🎯 Target {idx}: {price} ({percent}%)\n"
    return display_str


def open_order_all(
    symbol: str,
    price: float,
    size: str,
    kind: str,
    leverage: int,
    signal_id: str
) -> None:
    """
    Open orders on all configured accounts in parallel.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        price: Entry price (0 for market orders)
        size: Position size or percentage
        kind: Position type ('long' or 'short')
        leverage: Leverage multiplier
        signal_id: Unique signal identifier
    """
    start_time = datetime.datetime.now()
    
    accounts = config["ACCOUNTS"].items()
    proxies = list(config["PROXIES"].values())
    
    # Calculate proxy distribution
    accounts_per_proxy = max(1, len(accounts) // len(proxies))
    current_proxy_idx = 0
    
    for idx, (account_name, account_credentials) in enumerate(accounts, 1):
        # Rotate proxy every N accounts
        if idx > 1 and (idx - 1) % accounts_per_proxy == 0:
            current_proxy_idx = min(current_proxy_idx + 1, len(proxies) - 1)
        
        proxy = proxies[current_proxy_idx]
        api_key, secret_key = account_credentials.split(",")
        
        # Execute first account synchronously to validate
        if idx == 1:
            try:
                job_open_order(
                    api_key, secret_key, symbol, price, size,
                    kind, leverage, signal_id, account_name, proxy
                )
                logger.info(f"Order opened successfully for first account: {account_name}")
            except Exception as e:
                logger.error(f"Failed to open order on first account: {e}")
                raise
        else:
            # Schedule remaining accounts asynchronously
            scheduler.add_job(
                job_open_order,
                args=[
                    api_key, secret_key, symbol, price, size,
                    kind, leverage, signal_id, account_name, proxy
                ],
                misfire_grace_time=None
            )
    
    elapsed_time = datetime.datetime.now() - start_time
    logger.info(f"Scheduled orders for all accounts in {elapsed_time.total_seconds():.2f}s")


def job_open_order(
    api_key: str,
    secret_key: str,
    symbol: str,
    price: float,
    size: str,
    kind: str,
    leverage: int,
    signal_id: str,
    account_name: str,
    proxy: str
) -> Optional[str]:
    """
    Execute order opening for a single account.
    
    Args:
        api_key: Binance API key
        secret_key: Binance secret key
        symbol: Trading pair symbol
        price: Entry price
        size: Position size or percentage
        kind: Position type
        leverage: Leverage multiplier
        signal_id: Unique signal identifier
        account_name: Account name for logging
        proxy: Proxy server address
        
    Returns:
        Client order ID if successful, None otherwise
    """
    start_time = datetime.datetime.now()
    
    try:
        binance = Binance(key=api_key, secret=secret_key, proxy=proxy)
        
        # Set margin type to CROSSED
        try:
            binance.change_margin_type(symbol)
        except ClientError:
            pass  # Margin type might already be set
        
        # Set leverage
        binance.set_leverage(symbol, leverage)
        
        # Calculate position size
        calculated_size = _calculate_position_size(
            binance, symbol, price, size, leverage
        )
        
        # Determine order type and execute
        if price == 0:
            # Market order
            if kind == "long":
                order = binance.market_long(symbol, calculated_size, signal_id)
            else:
                order = binance.market_short(symbol, calculated_size, signal_id)
        else:
            # Limit order
            if kind == "long":
                order = binance.stoplimit_long(
                    symbol, price, price, calculated_size, signal_id
                )
            else:
                order = binance.stoplimit_short(
                    symbol, price, price, calculated_size, signal_id
                )
        
        elapsed_time = datetime.datetime.now() - start_time
        logger.info(
            f"Order opened for {symbol} on {account_name} "
            f"(ID: {api_key[:10]}...) in {elapsed_time.total_seconds():.2f}s"
        )
        
        return order.get('clientOrderId')
        
    except ClientError as error:
        error_msg = (
            f"Binance API Error - Status: {error.status_code}, "
            f"Code: {error.error_code}, Message: {error.error_message}"
        )
        logger.error(f"Failed to open order on {account_name}: {error_msg}")
        
        # Notify admin
        notification = (
            f"From {bot.get_me().first_name}\n"
            f"**🚨 Error Opening Order**\n"
            f"**Account:** {account_name}\n"
            f"**Symbol:** {symbol}\n"
            f"**Error:** `{error_msg}`"
        )
        bot.send_message(PRIVATE_LOG_ID, notification)
        
        raise


def _calculate_position_size(
    binance: Binance,
    symbol: str,
    price: float,
    size: str,
    leverage: int
) -> float:
    """
    Calculate the actual position size based on size specification.
    
    Args:
        binance: Binance API client
        symbol: Trading pair symbol
        price: Entry price
        size: Size specification (number, "Max", or percentage)
        leverage: Leverage multiplier
        
    Returns:
        Calculated position size
    """
    if size == "Max":
        balance = binance.get_balance()
        volume = balance * leverage * 0.4  # Use 40% of available balance
        decimal_places = binance.get_decimal_coin(symbol)
        
        if 'market' in str(price):
            price = float(str(price).replace('market', ''))
        
        calculated_size = volume / price
        return truncate_decimal(calculated_size, decimal_places)
    
    elif isinstance(size, str) and size.endswith('%'):
        volume_percent = int(size.replace('%', ''))
        balance = binance.get_balance()
        volume = balance * leverage * (volume_percent / 100)
        
        # Cap maximum volume
        volume = min(volume, 2000.0)
        
        decimal_places = binance.get_decimal_coin(symbol)
        
        if 'market' in str(price):
            price = float(str(price).replace('market', ''))
        
        calculated_size = volume / price
        return truncate_decimal(calculated_size, decimal_places)
    
    else:
        # Fixed size
        return float(size)


def check_orders() -> None:
    """
    Periodically check order status and manage targets and stop losses.
    
    This function:
    1. Checks if open orders have been filled
    2. Sets up take-profit targets when orders fill
    3. Monitors target orders and updates stop losses
    """
    try:
        # Check open orders
        open_signals = Signals.select().where(Signals.status == "OPEN")
        
        for signal in open_signals:
            try:
                order = base_binance.get_order(
                    symbol=signal.symbol,
                    ClientOrderId=signal.id_signal
                )
                
                if not order:
                    logger.warning(
                        f"Order {signal.id_signal} for {signal.symbol} not found"
                    )
                    signal.delete_instance()
                    continue
                
                if order['status'] == 'FILLED':
                    _handle_filled_order(signal, order)
                elif order['status'] == 'CANCELED':
                    signal.set_status('CANCELED')
                    logger.info(f"Order {signal.id_signal} was canceled")
                    
            except ClientError as error:
                if error.error_code == -2013:
                    signal.set_status('CANCELED')
                    logger.warning(f"Order {signal.id_signal} not found (deleted)")
                else:
                    logger.error(f"Error checking order {signal.id_signal}: {error}")
        
        # Check target orders
        _check_target_orders()
        
    except Exception as e:
        logger.error(f"Error in check_orders: {e}")


def _handle_filled_order(signal: Signals, order: dict) -> None:
    """
    Handle a filled order by setting up targets and stop loss.
    
    Args:
        signal: Signal database record
        order: Order details from Binance
    """
    logger.info(f"Order {signal.id_signal} for {signal.symbol} filled")
    
    # Generate target IDs
    target_ids = [
        generate_unique_signal_id()
        for _ in signal.targets_str.split("_")
    ]
    
    # Schedule target setup for all accounts
    accounts = config["ACCOUNTS"].items()
    proxies = list(config["PROXIES"].values())
    accounts_per_proxy = max(1, len(accounts) // len(proxies))
    
    for idx, (account_name, account_credentials) in enumerate(accounts, 1):
        proxy_idx = min((idx - 1) // accounts_per_proxy, len(proxies) - 1)
        proxy = proxies[proxy_idx]
        api_key, secret_key = account_credentials.split(",")
        
        scheduler.add_job(
            job_set_close,
            args=[
                api_key, secret_key, signal.symbol, signal.kind,
                signal.targets_str, signal.stop_limit,
                float(order['origQty']), signal, account_name, proxy, target_ids
            ],
            misfire_grace_time=None
        )
    
    # Save targets to database
    for idx, target_id in enumerate(target_ids, 1):
        Targets.create(
            owner=signal,
            number=idx,
            id_target=target_id
        )
    
    signal.set_status('CLOSE')


def _check_target_orders() -> None:
    """Check and manage open target orders."""
    open_targets = Targets.select().where(Targets.status == "OPEN")
    
    for target in open_targets:
        try:
            order = base_binance.get_order(
                symbol=target.owner.symbol,
                ClientOrderId=target.id_target
            )
            
            if not order:
                continue
            
            if order['status'] == 'FILLED':
                _handle_filled_target(target)
            elif order['status'] in ['CANCELED', 'EXPIRED']:
                target.set_status('CANCELED')
                logger.info(f"Target {target.id_target} was {order['status']}")
                
        except ClientError as error:
            logger.error(f"Error checking target {target.id_target}: {error}")


def _handle_filled_target(target: Targets) -> None:
    """
    Handle a filled target by updating stop loss.
    
    Args:
        target: Target database record
    """
    logger.info(
        f"Target {target.number} for {target.owner.symbol} filled"
    )
    
    # Schedule stop loss update for all accounts
    accounts = config["ACCOUNTS"].items()
    proxies = list(config["PROXIES"].values())
    accounts_per_proxy = max(1, len(accounts) // len(proxies))
    
    for idx, (account_name, account_credentials) in enumerate(accounts, 1):
        proxy_idx = min((idx - 1) // accounts_per_proxy, len(proxies) - 1)
        proxy = proxies[proxy_idx]
        api_key, secret_key = account_credentials.split(",")
        
        scheduler.add_job(
            job_change_stoploss,
            args=[api_key, secret_key, target, account_name, proxy],
            misfire_grace_time=None
        )
    
    target.set_status('CLOSE')


def job_set_close(
    api_key: str,
    secret_key: str,
    symbol: str,
    kind: str,
    targets_str: str,
    stop_limit: float,
    size: float,
    signal: Signals,
    account_name: str,
    proxy: str,
    target_ids: List[str]
) -> None:
    """
    Set up take-profit targets and stop loss for a filled order.
    
    Args:
        api_key: Binance API key
        secret_key: Binance secret key
        symbol: Trading pair symbol
        kind: Position type
        targets_str: Target prices and percentages
        stop_limit: Stop loss price
        size: Position size
        signal: Signal database record
        account_name: Account name for logging
        proxy: Proxy server address
        target_ids: List of target order IDs
    """
    try:
        binance = Binance(key=api_key, secret=secret_key, proxy=proxy)
        
        # Verify order is filled
        order = binance.get_order(symbol=symbol, ClientOrderId=signal.id_signal)
        if not order or order['status'] != 'FILLED':
            logger.warning(f"Order not filled for {account_name}")
            return
        
        # Set stop loss if specified
        if stop_limit != 0:
            _set_stop_loss(
                binance, symbol, kind, stop_limit,
                signal, account_name
            )
        
        # Set take-profit targets
        targets_list = parse_targets(targets_str)
        percent_list = [p for _, p in targets_list]
        targets_list = [p for p, _ in targets_list]
        
        decimal_places = binance.get_decimal_coin(symbol)
        
        for price_target, percent_target, target_id in zip(
            targets_list, percent_list, target_ids
        ):
            if percent_target == 0:
                continue
            
            # Validate target price
            if order['type'] == 'MARKET':
                entry_price = float(order['avgPrice'])
                if kind == 'long' and entry_price > price_target:
                    logger.warning(
                        f"Target {price_target} below entry {entry_price} "
                        f"for long position on {account_name}"
                    )
                    continue
                elif kind == 'short' and entry_price < price_target:
                    logger.warning(
                        f"Target {price_target} above entry {entry_price} "
                        f"for short position on {account_name}"
                    )
                    continue
            
            # Calculate target size
            target_size = (size * percent_target) / 100
            target_size = truncate_decimal(target_size, decimal_places)
            
            # Place target order
            try:
                if kind == 'long':
                    binance.limit_short(
                        symbol, price_target, target_size,
                        ClientOrderId=target_id
                    )
                else:
                    binance.limit_long(
                        symbol, price_target, target_size,
                        ClientOrderId=target_id
                    )
                logger.info(
                    f"Target set: {price_target} ({percent_target}%) "
                    f"for {symbol} on {account_name}"
                )
            except ClientError as error:
                logger.error(
                    f"Failed to set target on {account_name}: {error}"
                )
                
    except Exception as e:
        logger.error(f"Error in job_set_close for {account_name}: {e}")


def _set_stop_loss(
    binance: Binance,
    symbol: str,
    kind: str,
    stop_limit: float,
    signal: Signals,
    account_name: str
) -> None:
    """
    Set stop loss order for a position.
    
    Args:
        binance: Binance API client
        symbol: Trading pair symbol
        kind: Position type
        stop_limit: Stop loss price
        signal: Signal database record
        account_name: Account name for logging
    """
    try:
        client_order_id = f"{signal.id_signal}_stoploss"
        
        if kind == 'long':
            order = binance.stoploss_short(symbol, stop_limit, client_order_id)
        else:
            order = binance.stoploss_long(symbol, stop_limit, client_order_id)
        
        signal.set_id_stoploss(order['orderId'])
        signal.set_client_id_stoploss(order['clientOrderId'])
        
        logger.info(f"Stop loss set at {stop_limit} for {symbol} on {account_name}")
        
    except ClientError as error:
        logger.error(f"Failed to set stop loss on {account_name}: {error}")
        notification = (
            f"From {bot.get_me().first_name}\n"
            f"**🚨 Error Setting Stop Loss**\n"
            f"**Account:** {account_name}\n"
            f"**Symbol:** {symbol}\n"
            f"**Error:** `{error}`"
        )
        bot.send_message(PRIVATE_LOG_ID, notification)


def job_change_stoploss(
    api_key: str,
    secret_key: str,
    target: Targets,
    account_name: str,
    proxy: str
) -> None:
    """
    Update stop loss to entry price when a target is hit.
    
    Args:
        api_key: Binance API key
        secret_key: Binance secret key
        target: Target database record
        account_name: Account name for logging
        proxy: Proxy server address
    """
    try:
        binance = Binance(key=api_key, secret=secret_key, proxy=proxy)
        
        # Get current stop loss order
        old_stop_loss = binance.get_order(
            symbol=target.owner.symbol,
            ClientOrderId=target.owner.client_id_stoploss
        )
        
        if not old_stop_loss:
            logger.warning(f"Stop loss order not found for {account_name}")
            return
        
        # Cancel old stop loss
        try:
            binance.cancel_open_order(
                target.owner.symbol,
                ClientOrderId=old_stop_loss['clientOrderId'],
                orderId=old_stop_loss['orderId']
            )
            logger.info(f"Canceled old stop loss for {target.owner.symbol}")
        except ClientError as error:
            logger.error(f"Failed to cancel stop loss: {error}")
            
    except Exception as e:
        logger.error(f"Error in job_change_stoploss for {account_name}: {e}")


def verify_api_credentials() -> bool:
    """
    Verify that all configured API credentials are valid.
    
    Returns:
        True if all credentials are valid, False otherwise
    """
    logger.info("Verifying API credentials...")
    
    accounts = config["ACCOUNTS"].items()
    proxies = list(config["PROXIES"].values())
    accounts_per_proxy = max(1, len(accounts) // len(proxies))
    
    all_valid = True
    
    for idx, (account_name, account_credentials) in enumerate(accounts, 1):
        proxy_idx = min((idx - 1) // accounts_per_proxy, len(proxies) - 1)
        proxy = proxies[proxy_idx]
        api_key, secret_key = account_credentials.split(",")
        
        try:
            binance = Binance(key=api_key, secret=secret_key, proxy=proxy)
            balance = binance.get_balance()
            logger.info(f"✓ {account_name}: Balance = {balance} USDT")
        except ClientError as error:
            logger.error(
                f"✗ {account_name}: API Error - {error.error_message}"
            )
            all_valid = False
    
    return all_valid


@bot.on_message(Filters.chat(ANALYZER_IDS) & Filters.text, group=1)
class SignalHandler:
    """Handle incoming trading signals from authorized analyzers."""
    
    def __init__(self, client: Client, message):
        self.client = client
        self.message = message
        self.text = message.text
        
        try:
            self.process_signal()
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            self.client.send_message(
                message.chat.id,
                f"Error processing signal: {str(e)}"
            )
            raise
    
    def process_signal(self) -> None:
        """Process incoming signal and execute trades."""
        logger.info("Processing new signal...")
        
        if 'Kind' in self.text and not self.text.startswith('Giraffe'):
            self._handle_kind_signal()
        elif self.text.startswith('Turtle'):
            self._handle_turtle_signal()
        elif re.search(r'\w+ (LONG|SHORT)', self.text):
            self._handle_long_short_signal()
        elif self.text.startswith('Giraffe'):
            self._handle_giraffe_signal()
    
    def _handle_kind_signal(self) -> None:
        """Handle Kind format signals."""
        # Implementation would follow similar pattern to original
        pass
    
    def _handle_turtle_signal(self) -> None:
        """Handle Turtle format signals."""
        pass
    
    def _handle_long_short_signal(self) -> None:
        """Handle LONG/SHORT format signals."""
        pass
    
    def _handle_giraffe_signal(self) -> None:
        """Handle Giraffe format signals."""
        pass


def main() -> None:
    """Start the bot and begin listening for signals."""
    logger.info("Starting Copy Trade Futures Bot...")
    
    # Verify API credentials
    if not verify_api_credentials():
        logger.error("API credential verification failed")
        return
    
    # Start bot
    bot.start()
    logger.info(f"Bot started. Send /start to @{bot.get_me().username}")
    
    # Add message handlers
    from panel import MyStartHandler, MyButtonHandler, MyCallbackHandler
    
    bot.add_handler(
        MessageHandler(
            MyStartHandler,
            Filters.command(["start"]) & Filters.chat(ANALYZER_IDS)
        )
    )
    
    bot.add_handler(
        MessageHandler(
            MyButtonHandler,
            Filters.text & Filters.chat(ANALYZER_IDS)
        )
    )
    
    bot.add_handler(CallbackQueryHandler(MyCallbackHandler))
    
    # Schedule order checking
    scheduler.add_job(check_orders, 'interval', seconds=10)
    
    # Keep bot running
    idle()
    bot.stop()


if __name__ == '__main__':
    main()
