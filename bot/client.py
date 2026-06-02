"""
Binance API client wrapper.

Wraps the python-binance client configured specifically for
Binance Futures Testnet (USDT-M).
"""

import logging
import os

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv

from .logging_config import setup_logging

# Binance Futures Testnet base URLs
FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"

logger = setup_logging()


def _load_credentials() -> tuple[str, str]:
    """
    Load API credentials from environment variables (or .env file).

    Returns:
        (api_key, api_secret) tuple.

    Raises:
        EnvironmentError: if either credential is missing.
    """
    load_dotenv()

    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key:
        raise EnvironmentError(
            "BINANCE_API_KEY is not set. "
            "Create a .env file with BINANCE_API_KEY=<your_key>."
        )
    if not api_secret:
        raise EnvironmentError(
            "BINANCE_API_SECRET is not set. "
            "Create a .env file with BINANCE_API_SECRET=<your_secret>."
        )

    return api_key, api_secret


def get_futures_client() -> Client:
    """
    Create and return a python-binance Client pointed at the
    Binance Futures Testnet.

    The client is configured with:
    - testnet=True  → uses Binance Spot testnet endpoints
    - futures_url override → redirects all futures calls to
      https://testnet.binancefuture.com

    Returns:
        Configured binance.client.Client instance.

    Raises:
        EnvironmentError: if credentials are missing.
        BinanceAPIException / BinanceRequestException: on connectivity issues.
    """
    api_key, api_secret = _load_credentials()

    logger.info("Initialising Binance Futures Testnet client.")

    client = Client(
        api_key=api_key,
        api_secret=api_secret,
        testnet=True,
    )

    # Override futures base URL to point at the USDT-M futures testnet
    client.FUTURES_URL = FUTURES_TESTNET_BASE_URL + "/fapi"

    return client
