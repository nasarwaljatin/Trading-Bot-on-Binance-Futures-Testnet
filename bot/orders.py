"""
Order placement logic for Binance Futures Testnet.

Supports:
- MARKET orders
- LIMIT orders (GTC time-in-force)
"""

import logging
from typing import Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from .logging_config import setup_logging

logger = setup_logging()


def place_market_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
) -> dict:
    """
    Place a MARKET order on Binance Futures Testnet.

    Args:
        client:   Configured Binance futures client.
        symbol:   Trading pair (e.g. 'BTCUSDT').
        side:     'BUY' or 'SELL'.
        quantity: Order quantity.

    Returns:
        API response dict on success.

    Raises:
        BinanceAPIException: on API-level errors (e.g., invalid symbol).
        BinanceRequestException: on network / connectivity errors.
    """
    logger.info(
        "Placing MARKET %s order: symbol=%s, qty=%s",
        side,
        symbol,
        quantity,
    )

    response = client.futures_create_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=quantity,
    )

    logger.info("Order response: %s", response)
    return response


def place_limit_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    time_in_force: str = "GTC",
) -> dict:
    """
    Place a LIMIT order on Binance Futures Testnet.

    Args:
        client:        Configured Binance futures client.
        symbol:        Trading pair (e.g. 'BTCUSDT').
        side:          'BUY' or 'SELL'.
        quantity:      Order quantity.
        price:         Limit price.
        time_in_force: Defaults to 'GTC' (Good Till Cancelled).

    Returns:
        API response dict on success.

    Raises:
        BinanceAPIException: on API-level errors.
        BinanceRequestException: on network / connectivity errors.
    """
    logger.info(
        "Placing LIMIT %s order: symbol=%s, qty=%s, price=%s, tif=%s",
        side,
        symbol,
        quantity,
        price,
        time_in_force,
    )

    response = client.futures_create_order(
        symbol=symbol,
        side=side,
        type="LIMIT",
        quantity=quantity,
        price=price,
        timeInForce=time_in_force,
    )

    logger.info("Order response: %s", response)
    return response


def place_order(
    client: Client,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> dict:
    """
    Dispatch to the appropriate order placement function.

    Args:
        client:     Configured Binance futures client.
        symbol:     Trading pair (e.g. 'BTCUSDT').
        side:       'BUY' or 'SELL'.
        order_type: 'MARKET' or 'LIMIT'.
        quantity:   Order quantity.
        price:      Limit price (required for LIMIT orders).

    Returns:
        API response dict on success.

    Raises:
        ValueError: if order_type is unsupported.
        BinanceAPIException / BinanceRequestException: on API/network errors.
    """
    if order_type == "MARKET":
        return place_market_order(client, symbol, side, quantity)
    elif order_type == "LIMIT":
        return place_limit_order(client, symbol, side, quantity, price)
    else:
        raise ValueError(f"Unsupported order type: {order_type}")
