#!/usr/bin/env python3
"""Read-only MEXC Futures market snapshot."""

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


def positive(value, field):
    result = number(value, field)
    if result <= 0:
        raise MexcPublicError(f"{field} must be positive")
    return result


def unwrap(payload, label):
    if not isinstance(payload, dict):
        raise MexcPublicError(f"{label} must be an object")

    if payload.get("success") is False:
        raise MexcPublicError(
            f"MEXC {label} error: {payload.get('message', payload.get('code'))}"
        )

    data = payload.get("data", payload)
    if not isinstance(data, dict):
        raise MexcPublicError(f"invalid {label} data")

    return data


def run_snapshot(symbol="BTC_USDT", depth_limit=20, timeout=10):
    symbol = validate_symbol(symbol, futures=True)

    if depth_limit not in (5, 10, 20, 50, 100):
        raise MexcPublicError("depth limit must be 5, 10, 20, 50 or 100")

    ticker_response = public_get(
        "/api/v1/contract/ticker",
        {"symbol": symbol},
        timeout,
    )
    depth_response = public_get(
        f"/api/v1/contract/depth/{symbol}",
        {"limit": depth_limit},
        timeout,
    )
    funding_response = public_get(
        f"/api/v1/contract/funding_rate/{symbol}",
        timeout=timeout,
    )

    ticker = unwrap(ticker_response, "ticker")
    depth = unwrap(depth_response, "depth")
    funding = unwrap(funding_response, "funding rate")

    if ticker.get("symbol") != symbol:
        raise MexcPublicError("Futures ticker symbol mismatch")

    bid = positive(ticker.get("bid1"), "bid1")
    ask = positive(ticker.get("ask1"), "ask1")
    last = positive(ticker.get("lastPrice"), "lastPrice")

    if ask < bid:
        raise MexcPublicError("crossed Futures order book")

    bids = require_list(depth.get("bids"), "Futures depth bids")
    asks = require_list(depth.get("asks"), "Futures depth asks")

    if not bids or not asks:
        raise MexcPublicError("Futures order book is empty")

    normalized_bids = []
    normalized_asks = []

    for side, target in ((bids, normalized_bids), (asks, normalized_asks)):
        for level in side[:depth_limit]:
            if not isinstance(level, (list, tuple)) or len(level) < 2:
                raise MexcPublicError("invalid Futures order book level")

            target.append({
                "price": str(positive(level[0], "depth price")),
                "quantity": str(positive(level[1], "depth quantity")),
            })

    timestamp = depth.get("timestamp")
    if not isinstance(timestamp, int) or timestamp <= 0:
        raise MexcPublicError("missing or invalid Futures depth timestamp")

    funding_rate = number(funding.get("fundingRate"), "fundingRate")
    if funding_rate > 1:
        raise MexcPublicError("fundingRate is outside the accepted range")

    midpoint = (ask + bid) / Decimal("2")
    spread_bps = ((ask - bid) / midpoint) * Decimal("10000")

    return {
        "schema_version": 1,
        "source": "MEXC",
        "market_type": "perpetual",
        "mode": "public_read_only",
        "symbol": symbol,
        "timestamp_ms": timestamp,
        "bid": str(bid),
        "ask": str(ask),
        "last": str(last),
        "mark_price": str(positive(ticker.get("fairPrice"), "fairPrice"))
            if ticker.get("fairPrice") is not None else None,
        "index_price": str(positive(ticker.get("indexPrice"), "indexPrice"))
            if ticker.get("indexPrice") is not None else None,
        "spread_bps": str(spread_bps),
        "funding_rate": str(funding_rate),
        "open_interest_contracts": str(number(ticker.get("holdVol"), "holdVol")),
        "volume_24h_contracts": str(number(ticker.get("volume24"), "volume24")),
        "quote_volume_24h": str(number(ticker.get("amount24"), "amount24")),
        "next_funding_time_ms": funding.get("nextSettleTime"),
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
        description="MEXC Futures public market snapshot (read-only)"
    )
    parser.add_argument("--symbol", default="BTC_USDT")
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
        print("MEXC FUTURES · PUBLIC READ ONLY")
        print(f"Contract:     {result['symbol']}")
        print(f"Last:         {result['last']}")
        print(f"Best bid:     {result['bid']}")
        print(f"Best ask:     {result['ask']}")
        print(f"Spread:       {result['spread_bps']} bps")
        print(f"Funding rate: {result['funding_rate']}")
        print(f"Open interest:{result['open_interest_contracts']}")
        print(f"Depth levels: {result['depth']['limit']}")
        print("Account/API key: not accessed")
        print("Orders:          not enabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
