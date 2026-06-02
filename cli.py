"""
CLI entry point for the Binance Futures Testnet Trading Bot.

Usage:
    python cli.py --symbol <SYMBOL> --side <BUY|SELL> \
                  --type <MARKET|LIMIT> --quantity <QTY> [--price <PRICE>]
                  [--dry-run]

Examples:
    python cli.py --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.01
    python cli.py --symbol BTCUSDT --side BUY  --type LIMIT  --quantity 0.01 --price 60000
    python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.1
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT  --quantity 0.01 --price 70000

    # Demo mode (no API credentials required)
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --dry-run
"""

import argparse
import io
import random
import sys
import time

from binance.exceptions import BinanceAPIException, BinanceRequestException

from bot.client import get_futures_client
from bot.logging_config import setup_logging
from bot.orders import place_order
from bot.validators import ValidationError, validate_all

logger = setup_logging()

# ──────────────────────────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────────────────────────

_SEP = "=" * 60


def _print_request_summary(symbol: str, side: str, order_type: str,
                            quantity: float, price=None) -> None:
    print(_SEP)
    print("  ORDER REQUEST SUMMARY")
    print(_SEP)
    print(f"  Symbol   : {symbol}")
    print(f"  Side     : {side}")
    print(f"  Type     : {order_type}")
    print(f"  Quantity : {quantity}")
    if price is not None:
        print(f"  Price    : {price}")
    print(_SEP)
    print()


def _print_order_response(response: dict) -> None:
    print("[OK] Order placed successfully!")
    print()
    print(_SEP)
    print("  ORDER RESPONSE")
    print(_SEP)
    print(f"  Order ID     : {response.get('orderId', 'N/A')}")
    print(f"  Status       : {response.get('status', 'N/A')}")
    print(f"  Executed Qty : {response.get('executedQty', 'N/A')}")

    # Average fill price – present in MARKET fills, not always in LIMIT
    avg_price = response.get("avgPrice") or response.get("price", "N/A")
    print(f"  Avg Price    : {avg_price}")
    print(_SEP)


# ──────────────────────────────────────────────────────────────────────────────
# Dry-run mock
# ──────────────────────────────────────────────────────────────────────────────

# Realistic mid-market prices used for mock fills
_MOCK_PRICES = {
    "BTCUSDT":  67_250.40,
    "ETHUSDT":   3_512.80,
    "BNBUSDT":     605.15,
    "SOLUSDT":     165.32,
    "XRPUSDT":       0.5231,
}


def _mock_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
) -> dict:
    """
    Return a realistic-looking Binance Futures order response dict
    without making any real API call.
    """
    order_id = random.randint(3_000_000, 9_999_999)
    client_order_id = f"dryrun_{order_id}"
    ts = int(time.time() * 1000)

    base_price = _MOCK_PRICES.get(symbol, 1_000.0)
    # Simulate a small market slippage (±0.05 %)
    slippage = random.uniform(-0.0005, 0.0005)
    fill_price = round(base_price * (1 + slippage), 8)

    if order_type == "MARKET":
        return {
            "orderId": order_id,
            "symbol": symbol,
            "status": "FILLED",
            "clientOrderId": client_order_id,
            "price": "0",
            "avgPrice": f"{fill_price:.5f}",
            "origQty": str(quantity),
            "executedQty": str(quantity),
            "cumQuote": str(round(fill_price * quantity, 5)),
            "timeInForce": "GTC",
            "type": "MARKET",
            "side": side,
            "updateTime": ts,
        }
    else:  # LIMIT
        return {
            "orderId": order_id,
            "symbol": symbol,
            "status": "NEW",
            "clientOrderId": client_order_id,
            "price": str(price),
            "avgPrice": "0.00000",
            "origQty": str(quantity),
            "executedQty": "0.00",
            "cumQuote": "0.00000",
            "timeInForce": "GTC",
            "type": "LIMIT",
            "side": side,
            "updateTime": ts,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ──────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place Market or Limit orders on Binance Futures Testnet.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--symbol",
        required=True,
        metavar="SYMBOL",
        help="Trading pair symbol, e.g. BTCUSDT",
    )
    parser.add_argument(
        "--side",
        required=True,
        metavar="SIDE",
        help="Order side: BUY or SELL",
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        metavar="TYPE",
        help="Order type: MARKET or LIMIT",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        type=float,
        metavar="QTY",
        help="Order quantity (must be > 0)",
    )
    parser.add_argument(
        "--price",
        required=False,
        type=float,
        default=None,
        metavar="PRICE",
        help="Limit price (required for LIMIT orders, must be > 0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Simulate order placement without hitting the Binance API (no credentials needed)",
    )
    return parser


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> int:
    """
    Main entry point.

    Returns:
        0 on success, non-zero on failure.
    """
    parser = _build_parser()
    args = parser.parse_args()

    # Force UTF-8 output so special characters render on Windows terminals
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    # ── 1. Validate inputs ────────────────────────────────────────────────────
    try:
        params = validate_all(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValidationError as exc:
        print("[ERROR] Validation error: " + str(exc), file=sys.stderr)
        logger.error("Validation error: %s", exc)
        return 1

    symbol = params["symbol"]
    side = params["side"]
    order_type = params["order_type"]
    quantity = params["quantity"]
    price = params["price"]

    _print_request_summary(symbol, side, order_type, quantity, price)

    # ── 2. Dry-run path (no API credentials required) ─────────────────────────
    if args.dry_run:
        print("[DRY-RUN] Simulating order — no real API call will be made.\n")
        logger.info("[DRY-RUN] Simulating %s %s order: symbol=%s, qty=%s",
                    order_type, side, symbol, quantity)
        time.sleep(0.6)  # simulate slight network latency
        response = _mock_order(symbol, side, order_type, quantity, price)
        logger.info("[DRY-RUN] Mock response: %s", response)
        _print_order_response(response)
        return 0

    # ── 3. Initialise Binance client ──────────────────────────────────────────
    try:
        client = get_futures_client()
    except EnvironmentError as exc:
        print("[ERROR] Configuration error: " + str(exc), file=sys.stderr)
        logger.error("Configuration error: %s", exc)
        return 1

    # ── 4. Place the order ────────────────────────────────────────────────────
    try:
        response = place_order(
            client=client,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
    except BinanceAPIException as exc:
        msg = f"Binance API error [{exc.status_code}] code={exc.code}: {exc.message}"
        print(f"❌ {msg}", file=sys.stderr)
        logger.error(msg)
        return 1
    except BinanceRequestException as exc:
        msg = f"Network / connectivity error: {exc}"
        print(f"❌ {msg}", file=sys.stderr)
        logger.error(msg)
        return 1
    except Exception as exc:  # noqa: BLE001
        msg = f"Unexpected error: {exc}"
        print(f"❌ {msg}", file=sys.stderr)
        logger.exception(msg)
        return 1

    # ── 5. Display result ─────────────────────────────────────────────────────
    _print_order_response(response)
    return 0


if __name__ == "__main__":
    sys.exit(main())
