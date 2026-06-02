"""
Input validation helpers for CLI arguments.
All validation is performed client-side before any API call is made.
"""

from typing import Optional


class ValidationError(Exception):
    """Raised when user-supplied input fails validation."""


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise the trading pair symbol.

    Rules:
    - Must be a non-empty string.
    - Converted to uppercase.

    Returns the normalised symbol.
    Raises ValidationError on failure.
    """
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol must be a non-empty string (e.g. BTCUSDT).")
    normalised = symbol.strip().upper()
    if not normalised.isalnum():
        raise ValidationError(
            f"Symbol '{symbol}' contains invalid characters. "
            "Only alphanumeric characters are allowed (e.g. BTCUSDT)."
        )
    return normalised


def validate_side(side: str) -> str:
    """
    Validate the order side.

    Accepted values: BUY, SELL (case-insensitive).
    Returns uppercase side string.
    Raises ValidationError on failure.
    """
    if not side:
        raise ValidationError("Side must be specified (BUY or SELL).")
    normalised = side.strip().upper()
    if normalised not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return normalised


def validate_order_type(order_type: str) -> str:
    """
    Validate the order type.

    Accepted values: MARKET, LIMIT (case-insensitive).
    Returns uppercase order type string.
    Raises ValidationError on failure.
    """
    if not order_type:
        raise ValidationError("Order type must be specified (MARKET or LIMIT).")
    normalised = order_type.strip().upper()
    if normalised not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return normalised


def validate_quantity(quantity: float) -> float:
    """
    Validate the order quantity.

    Rules:
    - Must be a positive number (> 0).

    Returns the quantity as a float.
    Raises ValidationError on failure.
    """
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValidationError(
            f"Quantity must be greater than 0, got {qty}."
        )
    return qty


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate the order price.

    Rules:
    - Required for LIMIT orders (must be > 0).
    - Ignored / not required for MARKET orders.

    Returns the price as a float, or None for MARKET orders.
    Raises ValidationError on failure.
    """
    if order_type == "LIMIT":
        if price is None:
            raise ValidationError(
                "A --price must be supplied for LIMIT orders."
            )
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Price '{price}' is not a valid number.")
        if p <= 0:
            raise ValidationError(
                f"Price must be greater than 0, got {p}."
            )
        return p
    # MARKET order – price is irrelevant
    return None


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> dict:
    """
    Run all validations and return a dict of cleaned parameters.

    Raises ValidationError if any field is invalid.
    """
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, validate_order_type(order_type)),
    }
