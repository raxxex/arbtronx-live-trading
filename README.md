# ARBTRONX Live Trading Dashboard

🚀 **Professional cryptocurrency grid trading platform with mobile-responsive interface**

A sophisticated live trading dashboard for cryptocurrency grid trading with real-time market data, smart analysis, and automated trading capabilities.

## ✨ Features

- **📱 Mobile-Responsive**: Perfect interface for both desktop and mobile devices
- **💰 Live Trading**: Real-time trading with Binance API integration
- **🎯 4-Month Roadmap**: Structured progression from $200 to $100,000
- **🔲 Grid Trading**: Automated grid trading with smart volatility analysis
- **📊 Live Market Data**: Real-time price feeds for PEPE, FLOKI, DOGE, SHIB, SUI
- **🧠 Smart Analysis**: Volatility scoring and optimal grid spacing
- **⚡ Auto-Compound**: Automatic profit reinvestment
- **🛡️ Risk Management**: Built-in position sizing and stop-loss protection

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file with your Binance API credentials:
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
BINANCE_SANDBOX=false

USER_NAME=Your Name
USER_EMAIL=your@email.com
USER_ID=your_user_id
```

### 3. Start Trading Dashboard
```bash
python start_trading.py
```

### 4. Access Dashboard
Open http://localhost:8006 in your browser

## 📱 Mobile Ready

The dashboard is fully optimized for mobile devices with:
- Touch-friendly controls
- Responsive grid layouts
- PWA-ready interface
- Safe area support for mobile browsers

## 🎯 Trading Strategy

### Phase-Based Progression
- **Phase 1**: $200 → $1,000 (8 cycles @ 25% ROI)
- **Phase 2**: $1,000 → $5,000 (8 cycles @ 25% ROI)  
- **Phase 3**: $5,000 → $20,000 (6 cycles @ 25% ROI)
- **Phase 4**: $20,000 → $100,000 (6 cycles @ 20% ROI)

### Smart Grid Trading
- Volatility-based grid spacing
- Automatic level optimization
- Real-time market analysis
- Intelligent pair switching

## 🔧 Configuration

### API Key Setup
You can add API keys in two ways:

1. **Via .env file** (recommended for personal use)
2. **Via web interface** (click "🔑 Use Your API Keys" button)

### Supported Trading Pairs
- PEPE/USDT 🐸
- FLOKI/USDT 🐕
- DOGE/USDT 🐕
- SHIB/USDT 🐕
- SUI/USDT 💧

## 📊 Dashboard Features

### Live Market Data
- Real-time price updates
- 24h change tracking
- Portfolio value monitoring

### Smart Grid Analysis
- Volatility regime detection
- Optimal spacing calculation
- Confidence scoring
- Market overview

### Phase Tracking
- Current phase progress
- Cycle completion tracking
- ETA calculations
- Performance metrics

### Auto-Trading Controls
- One-click grid creation
- Smart trading activation
- Auto-compound toggle
- Emergency stop controls

## 🛡️ Safety Features

- **Live Trading Mode**: Clear indicators when using real funds
- **API Validation**: Automatic key verification
- **Error Handling**: Robust error recovery
- **Rate Limiting**: Respects exchange limits
- **Position Limits**: Configurable maximum sizes

## 📁 Project Structure

```
ARBTRONX/
├── live_dashboard.py      # Main dashboard application
├── start_trading.py       # Startup script
├── src/
│   ├── enhanced_binance_api.py    # Binance API wrapper
│   ├── smart_trading_engine.py    # Trading logic
│   ├── phase_based_trading.py     # Phase system
│   ├── exchanges/                 # Exchange integrations
│   ├── strategies/                # Trading strategies
│   ├── risk/                      # Risk management
│   └── utils/                     # Utility functions
├── static/                        # Logo and assets
├── requirements.txt               # Dependencies
└── README.md                      # This file
```

## ⚠️ Important Notes

- **Live Trading**: This system trades with real funds on Binance
- **Risk Warning**: Cryptocurrency trading involves substantial risk
- **API Security**: Keep your API keys secure and never share them
- **Testing**: Start with small amounts to test the system

## 🔗 Getting Help

1. Check the Binance API setup guide: `BINANCE_API_SETUP_GUIDE.md`
2. Review the documentation in the `docs/` folder
3. Ensure your API keys have the correct permissions

## 📄 License

MIT License - Use at your own risk. This software is for educational purposes.
