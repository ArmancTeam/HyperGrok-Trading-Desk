#!/usr/bin/env python3
"""Read-only MEXC Spot market snapshot."""

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation

from mexc_common import (
    MexcPublicError,
    public_get,
    require_list,
    validate_symbol,
)


def number(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise MexcPublicError(f"invalid numeric field: {field}")

    if not result.is_finite() or result < 0:
        raise MexcPublicError(f"invalid numeric field: {field}")

    return result


def signed_number(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise MexcPublicError(f"invalid numeric field: {field}")

    if not result.is_finite():
        raise MexcPublicError(f"invalid numeric field: {field}")

    return result


def positive(value, field):
    result = number(value, field)
    if result <= 0:
        raise MexcPublicError(f"{field} must be positive")
    return result


def run_snapshot(symbol="BTCUSDT", depth_limit=20, timeout=10):
    symbol = validate_symbol(symbol)

    if depth_limit not in (5, 10, 20, 50, 100):
        raise MexcPublicError("depth limit must be 5, 10, 20, 50 or 100")

    ticker = public_get(
        "/api/v3/ticker/24hr",
        {"symbol": symbol},
        timeout,
    )
    book = public_get(
        "/api/v3/ticker/bookTicker",
        {"symbol": symbol},
        timeout,
    )
    depth = public_get(
        "/api/v3/depth",
        {"symbol": symbol, "limit": depth_limit},
        timeout,
    )

    if not all(isinstance(item, dict) for item in (ticker, book, depth)):
        raise MexcPublicError("unexpected Spot response format")

    if ticker.get("symbol") != symbol:
        raise MexcPublicError("ticker symbol mismatch")

    bid = positive(book.get("bidPrice"), "bidPrice")
    ask = positive(book.get("askPrice"), "askPrice")
    last = positive(ticker.get("lastPrice"), "lastPrice")

    if ask < bid:
        raise MexcPublicError("crossed order book: ask is below bid")

    bids = require_list(depth.get("bids"), "depth bids")
    asks = require_list(depth.get("asks"), "depth asks")

    if not bids or not asks:
        raise MexcPublicError("order book is empty")

    normalized_bids = []
    normalized_asks = []

    for side, target in ((bids, normalized_bids), (asks, normalized_asks)):
        for level in side:
            if not isinstance(level, (list, tuple)) or len(level) < 2:
                raise MexcPublicError("invalid order book level")
            price = positive(level[0], "depth price")
            quantity = positive(level[1], "depth quantity")
            target.append({
                "price": str(price),
                "quantity": str(quantity),
            })

    timestamp = depth.get("timestamp")
    if not isinstance(timestamp, int) or timestamp <= 0:
        raise MexcPublicError("missing or invalid depth timestamp")

    spread_bps = ((ask - bid) / ((ask + bid) / 2)) * Decimal("10000")

    return {
        "schema_version": 1,
        "source": "MEXC",
        "market_type": "spot",
        "mode": "public_read_only",
        "symbol": symbol,
        "timestamp_ms": timestamp,
        "bid": str(bid),
        "ask": str(ask),
        "last": str(last),
        "bid_quantity": str(number(book.get("bidQty"), "bidQty")),
        "ask_quantity": str(number(book.get("askQty"), "askQty")),
        "spread_bps": str(spread_bps),
        "change_percent_24h": str(signed_number(ticker.get("priceChangePercent"), "priceChangePercent")),
        "base_volume_24h": str(number(ticker.get("volume"), "volume")),
        "quote_volume_24h": str(number(ticker.get("quoteVolume"), "quoteVolume")),
        "high_24h": str(positive(ticker.get("highPrice"), "highPrice")),
        "low_24h": str(positive(ticker.get("lowPrice"), "lowPrice")),
        "depth": {
            "limit": depth_limit,
            "bids": normalized_bids,
            "asks": normalized_asks,
        },
        "permissions": {
            "public_market_data": True,
            "account_access": False,
            "order_writes": False,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="MEXC Spot public market snapshot (read-only)"
    )
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--depth-limit", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = run_snapshot(args.symbol, args.depth_limit, args.timeout)
    except MexcPublicError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("MEXC SPOT · PUBLIC READ ONLY")
        print(f"Symbol:       {result['symbol']}")
        print(f"Last:         {result['last']}")
        print(f"Best bid:     {result['bid']}")
        print(f"Best ask:     {result['ask']}")
        print(f"Spread:       {result['spread_bps']} bps")
        print(f"24h change:   {result['change_percent_24h']}%")
        print(f"24h volume:   {result['quote_volume_24h']} quote")
        print(f"Depth levels: {result['depth']['limit']}")
        print("Account/API key: not accessed")
        print("Orders:          not enabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
