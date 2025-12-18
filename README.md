# Copy Trade Futures Bot

A production-grade Telegram bot that listens for trading signals and executes copy trades on multiple Binance Futures accounts simultaneously. This project demonstrates advanced Python development skills including async programming, API integration, database management, and real-time trading automation.

## 🎯 Project Overview

This bot was built to solve the problem of manually copying trading signals across multiple accounts. It:
- Listens for trading signals from authorized Telegram channels
- Parses multiple signal formats automatically
- Opens positions across 1000+ Binance Futures accounts in parallel
- Manages targets, stop losses, and position closing automatically
- Provides a real-time admin panel for monitoring and control

## ✨ Key Features

- **Multi-Format Signal Parsing**: Supports Kind, Turtle, LONG/SHORT, and Giraffe signal formats
- **Parallel Multi-Account Trading**: Opens positions across multiple accounts simultaneously using APScheduler
- **Automated Position Management**: Handles targets, stop losses, and position closing with precision
- **Admin Telegram Panel**: Real-time monitoring of positions, balances, and PNL
- **Proxy Support**: Distributes API calls across proxies to avoid rate limits
- **Database Persistence**: SQLite with Peewee ORM for signal and target tracking
- **Error Handling & Logging**: Comprehensive logging with colored output and error notifications
- **Docker Support**: Ready for containerized deployment

## 🏗️ Architecture

```
copy-trade-futures/
├── src/
│   ├── main.py              # Core bot logic and signal processing
│   ├── binance_api.py       # Binance Futures API wrapper
│   ├── models.py            # Database models (Signals, Targets, Settings)
│   ├── panel.py             # Telegram admin panel handlers
│   └── excel.py             # Excel data processing utilities
├── config/
│   ├── bot.ini              # Configuration (API keys, accounts, proxies)
│   └── bot.ini.example      # Configuration template
├── data/                    # Sample data files
├── logs/                    # Application logs
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Technical Stack

- **Language**: Python 3.8+
- **Telegram API**: Pyrogram (async Telegram client)
- **Exchange API**: Binance Futures Connector
- **Database**: SQLite with Peewee ORM
- **Task Scheduling**: APScheduler (background job execution)
- **Logging**: Coloredlogs (enhanced console output)
- **Containerization**: Docker & Docker Compose

## 📋 Signal Formats Supported

### Kind Signals
```
Symbol: BTC/USDT
Kind: long
Leverage: 10
Entry: 50000
Targets: 51000_25% 52000_25% 53000_50%
Sl: 49000
Vol: 100
```

### Turtle Signals
```
Turtle
BTC/USDT
Vol: 50
Sl: 49500
```

### LONG/SHORT Signals
```
BTC LONG
Leverage: 5
Entry: 50000
Targets: 51000
Stoploss: 49000
```

### Giraffe Signals
```
Giraffe
BTC/USDT
Leverage: 10
Entry: 50000
Targets: 51000_25% 52000_25% 53000_50%
Sl: 49000
Vol: 20%
```

## 🚀 Setup & Installation

### Prerequisites
- Python 3.8 or higher
- Binance Futures account(s) with API keys
- Telegram bot token (from BotFather)
- Telegram API credentials (api_id and api_hash)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/copy-trade-futures.git
cd copy-trade-futures
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure the Bot
```bash
cp config/bot.ini.example config/bot.ini
```

Edit `config/bot.ini` with your credentials:
```ini
[KEYS]
bot_token = YOUR_TELEGRAM_BOT_TOKEN
api_id = YOUR_TELEGRAM_API_ID
api_hash = YOUR_TELEGRAM_API_HASH

[TELEGRAM]
analyzers = ANALYZER_CHAT_ID_1,ANALYZER_CHAT_ID_2
private_log = YOUR_PRIVATE_LOG_CHANNEL_ID
public_log = YOUR_PUBLIC_LOG_CHANNEL_ID

[ACCOUNTS]
account1 = BINANCE_API_KEY,BINANCE_SECRET_KEY
account2 = BINANCE_API_KEY,BINANCE_SECRET_KEY

[PROXIES]
proxy1 = IP:PORT
proxy2 = IP:PORT
```

### Step 4: Run the Bot

**Option A: Direct Python**
```bash
python src/main.py
```

**Option B: Docker**
```bash
docker-compose up
```

## 🎮 Admin Commands

- `/start` - Show main menu
- `/set_target <price>` - Set custom target (reply to signal)
- `/set_stop <price>` - Set custom stop loss (reply to signal)
- `/limit_balance <amount>` - Set balance limit

## 🔐 Security Considerations

- **Never commit** `config/bot.ini` to version control (already in `.gitignore`)
- **Use environment variables** for sensitive data in production
- **Rotate API keys** regularly
- **Use proxies** to distribute API calls and avoid rate limits
- **Enable IP whitelist** on Binance API keys
- **Use read-only keys** where possible

## 📊 Database Schema

### Signals Table
- `id_signal`: Unique signal identifier
- `symbol`: Trading pair (e.g., BTCUSDT)
- `kind`: Position type (long/short)
- `entry`: Entry price
- `targets_str`: Target prices with percentages
- `stop_limit`: Stop loss price
- `status`: Signal status (OPEN/CLOSE/CANCELED)

### Targets Table
- `id_target`: Unique target identifier
- `owner`: Reference to Signal
- `number`: Target sequence number
- `status`: Target status (OPEN/CLOSE/CANCELED)

## 🔄 Workflow

1. **Signal Reception**: Bot listens to authorized Telegram channels
2. **Signal Parsing**: Extracts symbol, leverage, entry, targets, and stop loss
3. **Order Placement**: Opens positions across all configured accounts in parallel
4. **Order Tracking**: Monitors order status and fills
5. **Target Management**: Sets take-profit orders when position fills
6. **Stop Loss Management**: Sets stop loss orders and updates them as targets hit
7. **Position Closing**: Closes positions when all targets are hit or stop loss triggers

## 🧪 Testing

The project includes sample data in `data/sample.xlsx` for testing signal parsing logic.

## 📈 Performance Metrics

- **Parallel Account Execution**: Uses APScheduler for non-blocking concurrent order placement
- **API Rate Limiting**: Proxy rotation to distribute API calls
- **Database Optimization**: Indexed queries for fast signal/target lookups
- **Memory Efficient**: Streaming message processing without buffering

## 🐛 Troubleshooting

### Bot doesn't start
- Check `config/bot.ini` is properly configured
- Verify Telegram bot token is valid
- Ensure Binance API keys have futures trading enabled

### Orders not opening
- Check account balance
- Verify API key permissions (futures trading enabled)
- Check proxy connectivity
- Review logs for specific error messages

### Targets not setting
- Ensure position filled successfully
- Check target prices are valid (not below entry for long, not above for short)
- Verify account has sufficient balance for margin

## 📝 License

MIT License - See LICENSE file for details

## 👨‍💻 Author

**Shayan FH** - Full-stack developer specializing in trading automation and Python development

## 🤝 Contributing

This is a portfolio project. For improvements or suggestions, feel free to open an issue or submit a pull request.

## ⚠️ Disclaimer

This bot is for educational purposes only. Trading cryptocurrencies involves significant risk. Use at your own risk. The author is not responsible for any financial losses incurred through the use of this bot.

---

**Last Updated**: December 2024
