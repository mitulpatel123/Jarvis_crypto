# JARVIS Crypto Trading System

An AI-powered autonomous crypto trading system using Delta Exchange API and Groq AI.

## Overview

JARVIS is an intelligent, agent-based cryptocurrency trading system that leverages:
- **Delta Exchange API** for real-time market data and trade execution
- **Groq Cloud API** for AI-powered decision making
- **Multi-Agent Architecture** with 30+ specialized agents
- **Reinforcement Learning** for continuous improvement

## Features

- 🤖 **AI-Driven Trading**: Not rule-based, but powered by advanced AI models
- 📊 **Multi-Agent System**: 30+ specialized agents working in parallel
- ⚡ **Real-Time Analysis**: Continuous market monitoring 24/7
- 🎯 **Smart Decision Making**: Main Brain coordinates all agents for optimal decisions
- 🛡️ **Risk Management**: Built-in risk controls and position sizing
- 📈 **Technical Analysis**: RSI, MACD, Bollinger Bands, ATR, and more
- 📰 **Sentiment Analysis**: News and social media sentiment tracking
- 🔄 **Adaptive Learning**: Learns from past trades and market conditions

## Architecture

### Core Components

```
src/
├── agents/          # Specialized trading agents
│   ├── base_agent.py
│   ├── main_brain.py       # Central decision maker
│   ├── technical_agent.py   # Technical indicators
│   ├── trend_agent.py       # Trend analysis
│   ├── volatility_agent.py  # Volatility metrics
│   ├── volume_agent.py      # Volume analysis
│   ├── momentum_agent.py    # Momentum indicators
│   ├── pattern_agent.py     # Pattern recognition
│   ├── news_agent.py        # News sentiment
│   └── correlation_agent.py # Asset correlation
├── data/            # Data management
│   ├── delta_client.py      # Delta Exchange API
│   ├── groq_client.py       # Groq AI client
│   ├── pipeline.py          # Data pipeline
│   └── websocket_client.py  # Real-time data
├── execution/       # Trade execution
│   └── executor.py
├── risk/           # Risk management
│   └── risk_manager.py
└── dashboard/      # Monitoring UI
    └── app.py
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mitulpatel123/Jarvis_crypto.git
cd Jarvis_crypto
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file with:
```env
DELTA_API_KEY=your_delta_api_key
DELTA_API_SECRET=your_delta_api_secret
GROQ_API_KEY_1=your_groq_key_1
GROQ_API_KEY_2=your_groq_key_2
# Add more Groq keys for rotation
DATABASE_URL=your_database_url
```

## Usage

### Run the trading system:
```bash
python src/main.py
```

### Run verification scripts:
```bash
# Verify data pipeline
python scripts/verify_pipeline.py

# Verify execution system
python scripts/verify_execution.py
```

## Agent System

### Base Agents (20)
1. Technical Analysis Agent
2. Trend Following Agent
3. Volatility Agent
4. Volume Analysis Agent
5. Support/Resistance Agent
6. Pattern Recognition Agent
7. Momentum Agent
8. Correlation Agent
9. News Sentiment Agent
10. Risk Management Agent
11. Position Sizing Agent
12. Entry/Exit Signal Agent
13. Order Book Depth Agent
14. Economic Calendar Agent
15. Market Regime Agent
16. Mean Reversion Agent
17. Breakout Agent
18. Anomaly Detection Agent
19. Stop-Loss Optimization Agent
20. Trade History Agent

### Crypto-Specific Agents (10)
21. Funding Rate Agent
22. Liquidation Monitor Agent
23. Options Flow Agent
24. On-Chain Metrics Agent
25. Exchange Reserve Agent
26. Whale Movement Agent
27. Volatility Smile Agent
28. Staking/Unstaking Agent
29. Cross-Exchange Arbitrage Agent
30. Sentiment Aggregation Agent

## Data Sources

### Primary: Delta Exchange API (90%+)
- OHLC candles (1m to 1d)
- Real-time tickers
- Options Greeks
- Funding rates
- Open interest
- Order book depth
- Account data

### Secondary: Groq Browser Automation
- News sentiment
- Social media tracking
- On-chain metrics
- Economic calendar

### Tertiary: Free APIs
- CoinGecko
- DexScreener
- CoinMarketCap

## Risk Management

- Maximum daily loss limit: 2%
- Per-trade risk: 1% of capital
- ATR-based stop losses
- Dynamic position sizing
- Real-time monitoring

## Technology Stack

- **Language**: Python 3.8+
- **AI**: Groq Cloud API
- **Exchange**: Delta Exchange
- **Database**: PostgreSQL + TimescaleDB
- **Data Analysis**: pandas, numpy, ta-lib
- **Async**: asyncio, websockets
- **Testing**: pytest

## Development Roadmap

- [x] Phase 1: Foundation & Core Agents
- [x] Phase 2: Data Pipeline & Integration
- [x] Phase 3: Risk Management & Execution
- [ ] Phase 4: Advanced Agents & Learning
- [ ] Phase 5: Backtesting & Optimization
- [ ] Phase 6: Paper Trading
- [ ] Phase 7: Live Trading

## Contributing

This is a personal trading project. Contributions are not currently accepted.

## Disclaimer

This software is for educational purposes only. Cryptocurrency trading involves substantial risk. Use at your own risk. The authors are not responsible for any financial losses.

## License

Private - All Rights Reserved

## Contact

For inquiries: [Your Contact Information]
