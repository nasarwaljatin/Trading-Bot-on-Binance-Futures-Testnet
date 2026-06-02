# Binance Futures Testnet Trading Bot

A Python CLI application to place **Market** and **Limit** orders on Binance Futures Testnet (USDT-M) with structured logging, input validation, and clean error handling.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance API client wrapper
│   ├── orders.py          # Order placement logic
│   ├── validators.py      # Input validation helpers
│   └── logging_config.py  # Logging setup
├── cli.py                 # CLI entry point (argparse)
├── logs/
│   ├── market_order.log   # Sample MARKET order log
│   └── limit_order.log    # Sample LIMIT order log
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/trading-bot.git
cd trading-bot
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Binance Futures Testnet Credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Register / log in and generate your **API Key** and **Secret Key**
3. Create a `.env` file in the project root:

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

> **Note:** Never commit `.env` to version control. It is already listed in `.gitignore`.

---

## How to Run

### General Syntax

```bash
python cli.py --symbol <SYMBOL> --side <BUY|SELL> --type <MARKET|LIMIT> --quantity <QTY> [--price <PRICE>]
```

### Examples

**Place a MARKET BUY order**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

**Place a MARKET SELL order**
```bash
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.1
```

**Place a LIMIT BUY order**
```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 60000
```

**Place a LIMIT SELL order**
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 70000
```

### CLI Arguments

| Argument     | Required             | Description                              |
|--------------|----------------------|------------------------------------------|
| `--symbol`   | Yes                  | Trading pair (e.g., `BTCUSDT`)           |
| `--side`     | Yes                  | `BUY` or `SELL`                          |
| `--type`     | Yes                  | `MARKET` or `LIMIT`                      |
| `--quantity` | Yes                  | Order quantity (must be > 0)             |
| `--price`    | Yes (for LIMIT only) | Limit price (must be > 0)                |

---

## Sample Output

```
============================================================
  ORDER REQUEST SUMMARY
============================================================
  Symbol   : BTCUSDT
  Side     : BUY
  Type     : MARKET
  Quantity : 0.01
============================================================

✅ Order placed successfully!

============================================================
  ORDER RESPONSE
============================================================
  Order ID     : 3426251
  Status       : FILLED
  Executed Qty : 0.01
  Avg Price    : 63145.20
============================================================
```

---

## Logging

All API requests, responses, and errors are written to `logs/trading_bot.log`.

Log entries include:
- Timestamp and log level
- Outgoing request parameters
- Full API response payload
- Validation errors and API exceptions

**Sample log entry:**
```
2024-05-10 14:32:01,452 | INFO     | Placing MARKET BUY order: symbol=BTCUSDT, qty=0.01
2024-05-10 14:32:01,891 | INFO     | Order response: {'orderId': 3426251, 'status': 'FILLED', ...}
```

Pre-recorded log files from test runs are available in the `logs/` directory:
- `logs/market_order.log` — MARKET order run
- `logs/limit_order.log` — LIMIT order run

---

## Error Handling

The bot handles the following gracefully:

| Scenario                        | Behaviour                                      |
|---------------------------------|------------------------------------------------|
| Missing `--price` for LIMIT     | Validation error shown before API call         |
| Invalid side / order type       | Validation error shown before API call         |
| Non-positive quantity or price  | Validation error shown before API call         |
| Binance API error (e.g., -1121) | Error code and message displayed and logged    |
| Network / connectivity failure  | Timeout message displayed and logged           |

---

## Requirements

```
python-binance>=1.0.19
python-dotenv>=1.0.0
requests>=2.31.0
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Assumptions

- The bot targets **Binance Futures Testnet (USDT-M)** only; it is not configured for mainnet.
- Testnet base URL used: `https://testnet.binancefuture.com`
- All quantities and prices are accepted as floats and validated client-side before the API call.
- No position management or order tracking is implemented — this is a single-order placement tool.
- Time-in-force for LIMIT orders defaults to `GTC` (Good Till Cancelled).

