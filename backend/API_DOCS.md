# ARUN Titan Brain - API Documentation

Base URL: `http://localhost:8000`

## Status Endpoints

### `GET /`
Returns the operational status of the API.
**Response:**
```json
{
  "status": "online",
  "message": "ARUN Titan Brain is Active"
}
```

### `GET /health`
Checks connectivity to the SQLite database.
**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Data Endpoints

### `GET /api/positions`
Returns all currently open positions from the `trades.db`.
**Response:**
```json
[
  {
    "symbol": "TATASTEEL",
    "exchange": "NSE",
    "net_quantity": 10,
    "avg_entry_price": 150.5,
    "total_invested": 1505.0,
    "pnl_gross": 20.0,
    "current_price": 152.5
  }
]
```

### `GET /api/trades/recent`
Returns the 10 most recent trades.
**Query Params:**
- `limit` (optional, default=10): Number of trades to fetch.
