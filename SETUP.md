# Setup Guide - Copy Trade Futures Bot

This guide will help you set up and run the Copy Trade Futures Bot on your local machine or server.

## Prerequisites

Before you begin, ensure you have the following:

1. **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
2. **Binance Futures Account(s)** - [Create Account](https://www.binance.com/en/futures/BTCUSDT)
3. **Telegram Bot Token** - Create via [@BotFather](https://t.me/botfather)
4. **Telegram API Credentials** - Get from [my.telegram.org](https://my.telegram.org)
5. **Git** (optional) - For cloning the repository

## Step-by-Step Installation

### 1. Clone or Download the Repository

```bash
git clone https://github.com/yourusername/copy-trade-futures.git
cd copy-trade-futures
```

Or download as ZIP and extract.

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Bot

#### Copy the Example Configuration

```bash
cp config/bot.ini.example config/bot.ini
```

#### Edit `config/bot.ini`

Open `config/bot.ini` in your text editor and fill in your credentials:

```ini
[KEYS]
bot_token = YOUR_TELEGRAM_BOT_TOKEN_HERE
api_id = YOUR_TELEGRAM_API_ID_HERE
api_hash = YOUR_TELEGRAM_API_HASH_HERE

[TELEGRAM]
analyzers = ANALYZER_CHAT_ID_1,ANALYZER_CHAT_ID_2,ANALYZER_CHAT_ID_3
private_log = YOUR_PRIVATE_LOG_CHANNEL_ID
public_log = YOUR_PUBLIC_LOG_CHANNEL_ID

[ACCOUNTS]
account1 = BINANCE_API_KEY_1,BINANCE_SECRET_KEY_1
account2 = BINANCE_API_KEY_2,BINANCE_SECRET_KEY_2
account3 = BINANCE_API_KEY_3,BINANCE_SECRET_KEY_3

[PROXIES]
proxy1 = IP_ADDRESS:PORT
proxy2 = IP_ADDRESS:PORT
```

### 5. Get Your Credentials

#### Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the prompts to create a new bot
4. Copy the bot token provided

#### Telegram API Credentials

1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your Telegram account
3. Go to "API development tools"
4. Create a new application
5. Copy your `api_id` and `api_hash`

#### Binance API Keys

For each account you want to trade with:

1. Log in to [Binance Futures](https://www.binance.com/en/futures/BTCUSDT)
2. Go to Account → API Management
3. Create a new API key
4. **Enable Futures Trading** permission
5. Copy the API Key and Secret Key

**Security Tips:**
- Enable IP whitelist for your API keys
- Use read-only keys where possible
- Rotate keys regularly
- Never share your keys

#### Telegram Channel IDs

1. Create private Telegram channels for logging
2. Add your bot to these channels
3. Send a message to the channel
4. Forward the message to [@userinfobot](https://t.me/userinfobot)
5. Copy the channel ID (negative number)

#### Proxy Configuration (Optional)

If you have many accounts, use proxies to avoid rate limiting:

```ini
[PROXIES]
proxy1 = 192.168.1.1:8080
proxy2 = 192.168.1.2:8080
proxy3 = 192.168.1.3:8080
```

## Running the Bot

### Option 1: Direct Python Execution

```bash
python src/main.py
```

### Option 2: Docker (Recommended for Production)

```bash
docker-compose up
```

Or in detached mode:

```bash
docker-compose up -d
```

View logs:

```bash
docker-compose logs -f
```

Stop the bot:

```bash
docker-compose down
```

## Verification

After starting the bot, verify it's working:

1. Send `/start` to your bot on Telegram
2. You should see the main menu
3. Check the logs for any errors

## Troubleshooting

### Bot doesn't start

**Error:** `ModuleNotFoundError: No module named 'pyrogram'`

**Solution:** Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Connection refused

**Error:** `ConnectionError: Failed to connect to Binance API`

**Solution:**
- Check your internet connection
- Verify API keys are correct
- Check if Binance API is accessible from your location
- Try using a proxy

### Invalid API Key

**Error:** `binance.error.ClientError: Invalid API key`

**Solution:**
- Verify the API key is correct in `config/bot.ini`
- Check if the API key is still valid (not deleted)
- Ensure the API key has Futures Trading enabled
- Check IP whitelist settings

### Telegram authentication failed

**Error:** `pyrogram.errors.Unauthorized`

**Solution:**
- Verify `bot_token`, `api_id`, and `api_hash` are correct
- Ensure the bot token hasn't expired
- Check if the bot is still active in BotFather

### No signals received

**Possible causes:**
- Analyzer chat IDs are incorrect
- Bot is not in the analyzer channels
- Signal format doesn't match expected patterns

**Solution:**
- Verify analyzer IDs in `config/bot.ini`
- Add bot to analyzer channels
- Check signal format matches documentation

## Database

The bot uses SQLite for data persistence. The database file is created automatically:

```
db  # SQLite database file
```

To reset the database:

```bash
rm db
python src/main.py  # Will recreate the database
```

## Logs

Logs are stored in the `logs/` directory:

```
logs/
├── pnls.txt          # PNL records
└── [other logs]
```

## Security Best Practices

1. **Never commit `config/bot.ini`** - It's already in `.gitignore`
2. **Use environment variables** for production:
   ```bash
   export BOT_TOKEN="your_token"
   export API_ID="your_id"
   # etc.
   ```
3. **Rotate API keys** regularly
4. **Use IP whitelist** on Binance API keys
5. **Monitor logs** for suspicious activity
6. **Use proxies** to distribute API calls
7. **Enable 2FA** on your Binance account

## Performance Optimization

For large numbers of accounts:

1. **Use multiple proxies** - Distribute API calls
2. **Increase scheduler interval** - Adjust in `src/main.py`
3. **Use SSD** - Faster database operations
4. **Monitor memory** - Check for memory leaks

## Advanced Configuration

### Custom Signal Formats

Edit `src/main.py` to add custom signal parsing logic in the `Halakui` class.

### Database Optimization

For high-frequency trading, consider:
- Increasing SQLite cache size
- Using connection pooling
- Archiving old signals

### Scaling

For 1000+ accounts:
- Use multiple bot instances
- Implement load balancing
- Use message queue (RabbitMQ, Redis)

## Support

For issues or questions:

1. Check the [README.md](README.md)
2. Review the [troubleshooting section](#troubleshooting)
3. Check logs in `logs/` directory
4. Open an issue on GitHub

## Next Steps

1. ✅ Complete setup
2. 📝 Test with a small number of accounts
3. 📊 Monitor performance
4. 🚀 Scale up gradually
5. 🔒 Implement additional security measures

---

**Last Updated:** December 2024
