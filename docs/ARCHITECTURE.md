# CEX Arbitrage Bot Architecture

## Overview

The CEX Arbitrage Bot is designed with a modular, scalable architecture that separates concerns and allows for easy maintenance and extension.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CEX Arbitrage Bot                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Main Bot  │  │  Dashboard  │  │    Notifications    │  │
│  │   (main.py) │  │   Backend   │  │     (Telegram/      │  │
│  │             │  │  (FastAPI)  │  │      Slack)         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Arbitrage  │  │  Exchange   │  │      Database       │  │
│  │   Engine    │  │   Manager   │  │    (SQLAlchemy)     │  │
│  │             │  │             │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐                          │
│  │   KuCoin    │  │     OKX     │                          │
│  │  Exchange   │  │  Exchange   │                          │
│  │             │  │             │                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Main Bot (`main.py`)

The entry point that orchestrates all components:

- **Responsibilities:**
  - Initialize database
  - Start the arbitrage bot
  - Handle shutdown gracefully
  - Configure logging

- **Key Features:**
  - Signal handling for clean shutdown
  - Error handling and recovery
  - Logging configuration

### 2. Arbitrage Engine (`src/arbitrage/`)

The core trading logic:

#### Bot Manager (`bot.py`)
- Orchestrates scanning and execution
- Manages bot lifecycle
- Handles auto-execution logic

#### Scanner (`scanner.py`)
- Continuously scans for opportunities
- Manages WebSocket connections
- Caches market data

#### Calculator (`calculator.py`)
- Calculates arbitrage opportunities
- Considers fees and slippage
- Validates profitability

#### Executor (`executor.py`)
- Executes arbitrage trades
- Manages concurrent executions
- Handles trade failures

#### Opportunity Models (`opportunity.py`)
- Data structures for opportunities
- Profit calculations
- Validation logic

### 3. Exchange Manager (`src/exchanges/`)

Handles all exchange interactions:

#### Base Exchange (`base.py`)
- Abstract interface for exchanges
- Common data structures
- Standardized methods

#### KuCoin Exchange (`kucoin_exchange.py`)
- KuCoin-specific implementation
- REST API and WebSocket handling
- Order management

#### OKX Exchange (`okx_exchange.py`)
- OKX-specific implementation
- REST API and WebSocket handling
- Order management

#### Exchange Manager (`exchange_manager.py`)
- Manages multiple exchanges
- Coordinates data fetching
- Handles failover

### 4. Database Layer (`src/database/`)

Data persistence and management:

#### Models (`models.py`)
- SQLAlchemy ORM models
- Database schema definitions
- Data access methods

#### Database Manager
- High-level database operations
- Logging and analytics
- Data aggregation

### 5. Notification System (`src/notifications/`)

Alert and notification handling:

#### Telegram Notifier (`telegram.py`)
- Telegram bot integration
- Message formatting
- Error handling

#### Slack Notifier (`slack.py`)
- Slack webhook integration
- Rich message formatting
- Channel management

#### Notification Manager (`manager.py`)
- Coordinates all notification services
- Rate limiting
- Message routing

### 6. Dashboard (`src/dashboard/`)

Web-based monitoring interface:

#### Backend (`backend/app.py`)
- FastAPI REST API
- WebSocket real-time updates
- Data aggregation

#### Frontend (`frontend/`)
- React-based UI
- Real-time data visualization
- Interactive controls

## Data Flow

### 1. Market Data Flow

```
Exchange APIs → WebSocket → Exchange Manager → Scanner → Calculator
```

1. **Data Ingestion:** WebSocket connections receive real-time market data
2. **Normalization:** Exchange-specific data is normalized to common format
3. **Caching:** Recent data is cached for fast access
4. **Analysis:** Scanner analyzes data for opportunities

### 2. Opportunity Detection Flow

```
Market Data → Calculator → Opportunity → Validator → Executor
```

1. **Calculation:** Calculator computes spreads and profits
2. **Validation:** Opportunities are validated against thresholds
3. **Ranking:** Opportunities are ranked by profitability
4. **Execution:** Best opportunities are executed

### 3. Trade Execution Flow

```
Opportunity → Balance Check → Order Placement → Result Processing → Logging
```

1. **Pre-flight:** Check balances and validate opportunity
2. **Execution:** Place simultaneous buy/sell orders
3. **Monitoring:** Track order status and completion
4. **Logging:** Record results and update statistics

## Design Patterns

### 1. Strategy Pattern

Used for exchange implementations:
- Common interface (`BaseExchange`)
- Exchange-specific strategies (`KuCoinExchange`, `OKXExchange`)
- Easy to add new exchanges

### 2. Observer Pattern

Used for real-time updates:
- WebSocket connections observe market changes
- Dashboard observes bot state changes
- Notifications observe trade events

### 3. Factory Pattern

Used for creating exchange instances:
- `ExchangeManager` creates appropriate exchange objects
- Configuration-driven instantiation
- Easy testing with mock objects

### 4. Singleton Pattern

Used for global configuration:
- Settings object provides global configuration
- Database connection management
- Logging configuration

## Scalability Considerations

### 1. Horizontal Scaling

- **Multiple Bot Instances:** Run multiple bots with different trading pairs
- **Load Balancing:** Distribute API calls across multiple instances
- **Database Sharding:** Partition data by exchange or time period

### 2. Vertical Scaling

- **Async Operations:** All I/O operations are asynchronous
- **Connection Pooling:** Efficient database connection management
- **Caching:** In-memory caching of frequently accessed data

### 3. Performance Optimization

- **WebSocket Connections:** Real-time data reduces API calls
- **Batch Operations:** Group database operations for efficiency
- **Lazy Loading:** Load data only when needed

## Security Architecture

### 1. API Key Management

- Environment variable storage
- No hardcoded credentials
- Separate keys for different environments

### 2. Network Security

- HTTPS for all external communications
- WebSocket secure connections (WSS)
- IP whitelisting for exchange APIs

### 3. Data Protection

- Encrypted database connections
- Secure session management
- Input validation and sanitization

## Error Handling Strategy

### 1. Graceful Degradation

- Continue operation with reduced functionality
- Fallback to cached data when APIs fail
- Automatic retry with exponential backoff

### 2. Circuit Breaker Pattern

- Stop calling failing services temporarily
- Monitor service health
- Automatic recovery when services restore

### 3. Comprehensive Logging

- Structured logging with context
- Error tracking and alerting
- Performance monitoring

## Testing Strategy

### 1. Unit Tests

- Individual component testing
- Mock external dependencies
- High code coverage

### 2. Integration Tests

- End-to-end workflow testing
- Real API interactions (sandbox)
- Database integration testing

### 3. Performance Tests

- Load testing for high-frequency scenarios
- Memory usage monitoring
- Latency measurement

## Deployment Architecture

### 1. Development Environment

- Local development with simulation mode
- Hot reloading for rapid iteration
- Comprehensive logging

### 2. Staging Environment

- Sandbox API integration
- Full feature testing
- Performance validation

### 3. Production Environment

- Live API integration
- Monitoring and alerting
- Backup and recovery procedures

## Future Enhancements

### 1. Additional Exchanges

- Binance integration
- Coinbase Pro integration
- Kraken integration

### 2. Advanced Features

- Machine learning for opportunity prediction
- Risk management improvements
- Portfolio optimization

### 3. Infrastructure

- Kubernetes deployment
- Microservices architecture
- Event-driven architecture
