# CEX Arbitrage Bot Setup Guide

## Prerequisites

- Python 3.9 or higher
- Node.js 16 or higher (for dashboard frontend)
- Git

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd CEX_Arbitrage
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies (Optional)

If you want to run the React dashboard:

```bash
cd src/dashboard/frontend
npm install
cd ../../..
```

## Configuration

### 1. Environment Variables

Copy the environment template and configure your settings:

```bash
cp .env.template .env
```

Edit the `.env` file with your configuration:

```env
# Exchange API Keys
KUCOIN_API_KEY=your_kucoin_api_key_here
KUCOIN_SECRET_KEY=your_kucoin_secret_key_here
KUCOIN_PASSPHRASE=your_kucoin_passphrase_here

OKX_API_KEY=your_okx_api_key_here
OKX_SECRET_KEY=your_okx_secret_key_here
OKX_PASSPHRASE=your_okx_passphrase_here

# Trading Configuration
MIN_PROFIT_THRESHOLD=0.5
MAX_TRADE_SIZE_USD=1000
SIMULATION_MODE=true

# Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

### 2. Exchange API Setup

#### KuCoin API Setup

1. Go to [KuCoin API Management](https://www.kucoin.com/account/api)
2. Create a new API key with the following permissions:
   - General
   - Trade
   - Transfer (if needed)
3. Note down the API Key, Secret, and Passphrase
4. For testing, enable sandbox mode

#### OKX API Setup

1. Go to [OKX API Management](https://www.okx.com/account/my-api)
2. Create a new API key with the following permissions:
   - Read
   - Trade
3. Note down the API Key, Secret, and Passphrase
4. For testing, enable demo trading

### 3. Notification Setup (Optional)

#### Telegram Setup

1. Create a new bot by messaging [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Get your bot token
4. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)

#### Slack Setup

1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new app
3. Enable Incoming Webhooks
4. Create a webhook URL for your channel

## Database Setup

The bot uses SQLite by default. The database will be created automatically when you first run the bot.

For production, you can use PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost/arbitrage_bot
```

## Running the Bot

### 1. Start the Main Bot

```bash
python main.py
```

### 2. Start the Dashboard (Optional)

In a separate terminal:

```bash
python -m src.dashboard.backend.app
```

The dashboard will be available at `http://localhost:8000`

### 3. Start the Frontend (Optional)

In another terminal:

```bash
cd src/dashboard/frontend
npm run dev
```

The React frontend will be available at `http://localhost:3000`

## Testing

### Run Unit Tests

```bash
pytest
```

### Run Specific Tests

```bash
pytest tests/test_arbitrage_calculator.py
pytest tests/test_exchange_manager.py -v
```

### Run with Coverage

```bash
pytest --cov=src tests/
```

## Monitoring

### Logs

Logs are stored in the `logs/` directory:

- `logs/arbitrage_bot.log`: Main application logs
- Console output for real-time monitoring

### Dashboard

Access the web dashboard at `http://localhost:8000` to monitor:

- Bot status and statistics
- Live arbitrage opportunities
- Recent trade executions
- Exchange balances

### Notifications

If configured, you'll receive notifications for:

- Successful trade executions
- Failed trade executions
- System errors
- Daily profit summaries

## Troubleshooting

### Common Issues

#### 1. API Connection Errors

```
Error: Failed to connect to KuCoin: Invalid API key
```

**Solution:**
- Verify your API keys are correct
- Check if API key permissions are sufficient
- Ensure you're using the correct sandbox/production settings

#### 2. Insufficient Balance

```
Error: Insufficient USDT on kucoin: need 1000.00, have 500.00
```

**Solution:**
- Add more funds to your exchange accounts
- Reduce the `MAX_TRADE_SIZE_USD` setting
- Enable simulation mode for testing

#### 3. No Opportunities Found

```
Info: Found 0 arbitrage opportunities
```

**Solution:**
- Lower the `MIN_PROFIT_THRESHOLD`
- Check if exchanges are connected
- Verify trading pairs are available on both exchanges

#### 4. WebSocket Connection Issues

```
Error: WebSocket error for KuCoin: Connection failed
```

**Solution:**
- Check your internet connection
- Verify firewall settings
- Try restarting the bot

### Debug Mode

Enable debug mode for more detailed logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Support

For additional support:

1. Check the logs in `logs/arbitrage_bot.log`
2. Review the configuration in `.env`
3. Test API connections manually
4. Check exchange status pages for outages

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Enable IP restrictions** on exchange API keys
4. **Start with simulation mode** before live trading
5. **Use small amounts** for initial testing
6. **Monitor trades closely** when starting
7. **Keep software updated** regularly

## Performance Optimization

1. **Adjust scan intervals** based on your needs
2. **Optimize trading pairs** selection
3. **Monitor system resources** usage
4. **Use SSD storage** for better database performance
5. **Consider VPS deployment** for 24/7 operation
