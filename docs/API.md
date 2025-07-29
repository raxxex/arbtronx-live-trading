# CEX Arbitrage Bot API Documentation

## Overview

The CEX Arbitrage Bot provides a RESTful API and WebSocket interface for monitoring and controlling the arbitrage trading bot.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, implement proper authentication mechanisms.

## REST API Endpoints

### Bot Status

#### GET /api/status

Get current bot status and statistics.

**Response:**
```json
{
  "running": true,
  "uptime": 3600.5,
  "auto_execute": true,
  "simulation_mode": true,
  "exchanges_connected": 2,
  "scan_count": 1500,
  "opportunities_found": 45,
  "current_opportunities": 3,
  "total_executions": 12,
  "successful_executions": 10,
  "success_rate": 83.3,
  "total_profit": 125.50,
  "last_execution_time": 1234567890
}
```

### Arbitrage Opportunities

#### GET /api/opportunities

Get current arbitrage opportunities.

**Response:**
```json
[
  {
    "symbol": "BTC/USDT",
    "buy_exchange": "kucoin",
    "sell_exchange": "okx",
    "buy_price": 50000.0,
    "sell_price": 50100.0,
    "spread_percentage": 0.2,
    "profit_usd": 10.0,
    "net_profit": 9.8,
    "volume": 1.0,
    "timestamp": 1234567890000
  }
]
```

### Trade Executions

#### GET /api/executions

Get recent trade executions.

**Parameters:**
- `limit` (optional): Number of executions to return (default: 10)

**Response:**
```json
[
  {
    "success": true,
    "symbol": "BTC/USDT",
    "buy_exchange": "kucoin",
    "sell_exchange": "okx",
    "expected_profit": 10.0,
    "actual_profit": 9.5,
    "execution_time": 2.5,
    "error_message": null,
    "buy_trade_id": "12345",
    "sell_trade_id": "67890"
  }
]
```

### Manual Execution

#### POST /api/execute/{symbol}

Manually execute arbitrage for a specific symbol.

**Parameters:**
- `symbol`: Trading pair symbol (e.g., "BTC/USDT")

**Response:**
```json
{
  "success": true,
  "actual_profit": 9.5,
  "execution_time": 2.5,
  "error_message": null
}
```

### Settings

#### POST /api/settings

Update bot settings.

**Request Body:**
```json
{
  "min_profit_threshold": 0.5,
  "max_trade_size_usd": 1000.0,
  "auto_execute": true
}
```

**Response:**
```json
{
  "message": "Settings updated successfully"
}
```

### Notifications

#### POST /api/test-notifications

Test notification services.

**Response:**
```json
{
  "results": {
    "telegram": true,
    "slack": false
  }
}
```

## WebSocket API

### Connection

Connect to the WebSocket endpoint for real-time updates:

```
ws://localhost:8000/ws
```

### Message Format

All WebSocket messages follow this format:

```json
{
  "type": "message_type",
  "data": { ... }
}
```

### Message Types

#### Status Updates

```json
{
  "type": "status",
  "data": {
    "running": true,
    "uptime": 3600.5,
    "total_profit": 125.50,
    ...
  }
}
```

#### Opportunities Updates

```json
{
  "type": "opportunities",
  "data": [
    {
      "symbol": "BTC/USDT",
      "buy_exchange": "kucoin",
      "sell_exchange": "okx",
      ...
    }
  ]
}
```

#### Executions Updates

```json
{
  "type": "executions",
  "data": [
    {
      "success": true,
      "symbol": "BTC/USDT",
      "actual_profit": 9.5,
      ...
    }
  ]
}
```

#### Combined Updates

```json
{
  "type": "update",
  "status": { ... },
  "opportunities": [ ... ],
  "executions": [ ... ]
}
```

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Bot not initialized

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## Examples

### Python Client Example

```python
import asyncio
import aiohttp
import websockets
import json

async def get_bot_status():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/api/status') as response:
            return await response.json()

async def listen_to_updates():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data['type']}")

# Usage
status = asyncio.run(get_bot_status())
print(status)
```

### JavaScript Client Example

```javascript
// REST API
fetch('http://localhost:8000/api/status')
  .then(response => response.json())
  .then(data => console.log(data));

// WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received:', data.type);
};
```

## Security Considerations

1. **Authentication**: Implement proper authentication for production
2. **HTTPS**: Use HTTPS in production environments
3. **CORS**: Configure CORS properly for your domain
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Input Validation**: Validate all input parameters
6. **API Keys**: Never expose API keys in client-side code
