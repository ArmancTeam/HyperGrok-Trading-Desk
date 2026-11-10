#!/usr/bin/env python3
"""MEXC Spot and Futures authenticated account balance reader."""

import argparse
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation

from mexc_auth import (
    MexcAuthError,
    signed_spot_get,
    signed_futures_get,
)


def amount(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise MexcAuthError(f"invalid account field: {field}")

    if not result.is_finite() or result < 0:
        raise MexcAuthError(f"invalid account field: {field}")

    return result


def signed_amount(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise MexcAuthError(f"invalid account field: {field}")

    if not result.is_finite():
        raise MexcAuthError(f"invalid account field: {field}")

    return result


def read_spot(api_key, api_secret, timeout=10):
    payload = signed_spot_get(
        "/api/v3/account",
        {},
        api_key,
        api_secret,
        timeout=timeout,
    )

    if not isinstance(payload, dict):
        raise MexcAuthError("invalid Spot account response")

    if payload.get("code") not in (None, 0, "0", "200"):
        raise MexcAuthError("MEXC Spot account request failed")

    balances = payload.get("balances")
    if not isinstance(balances, list):
        raise MexcAuthError("Spot balances are missing")

    result = []

    for item in balances:
        if not isinstance(item, dict):
            raise MexcAuthError("invalid Spot balance entry")

        asset = item.get("asset")
        if not isinstance(asset, str) or not re.fullmatch(
            r"[A-Z0-9]{2,20}", asset
        ):
            raise MexcAuthError("invalid Spot asset")

        free = amount(item.get("free"), "free")
        locked = amount(item.get("locked"), "locked")

        if free or locked:
            result.append({
                "asset": asset,
                "free": str(free),
                "locked": str(locked),
                "total": str(free + locked),
            })

    return {
        "market_type": "spot",
        "balances": result,
    }


def read_futures(
    api_key, api_secret, currency="USDT", timeout=10
):
    currency = currency.strip().upper()

    if not re.fullmatch(r"[A-Z0-9]{2,20}", currency):
        raise MexcAuthError("invalid Futures currency")

    payload = signed_futures_get(
        f"/api/v1/private/account/asset/{currency}",
        {},
        api_key,
        api_secret,
        timeout=timeout,
    )

    if not isinstance(payload, dict):
        raise MexcAuthError("invalid Futures account response")

    if payload.get("success") is not True:
        raise MexcAuthError("MEXC Futures account request failed")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise MexcAuthError("Futures account data is missing")

    returned_currency = data.get("currency")
    if returned_currency != currency:
        raise MexcAuthError("Futures currency mismatch")

    fields = (
        "availableBalance",
        "cashBalance",
        "frozenBalance",
        "equity",
        "unrealized",
        "positionMargin",
    )

    result = {"currency": currency}

    for field in fields:
        parser = signed_amount if field == "unrealized" else amount
        result[field] = str(parser(data.get(field), field))

    return {
        "market_type": "futures",
        "balance": result,
    }


def run_account(currency="USDT", timeout=10):
    api_key = os.environ.get("MEXC_API_KEY")
    api_secret = os.environ.get("MEXC_API_SECRET")

    if not api_key or not api_secret:
        raise MexcAuthError(
            "Set MEXC_API_KEY and MEXC_API_SECRET environment variables"
        )

    spot = read_spot(api_key, api_secret, timeout)
    futures = read_futures(
        api_key, api_secret, currency, timeout
    )

    return {
        "schema_version": 1,
        "source": "MEXC",
        "mode": "authenticated_read_only",
        "spot": spot,
        "futures": futures,
        "permissions": {
            "spot_account_read": True,
            "futures_account_read": True,
            "order_writes": False,
            "transfers": False,
            "withdrawals": False,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="MEXC authenticated read-only account balances"
    )
    parser.add_argument("--futures-currency", default="USDT")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = run_account(
            args.futures_currency,
            args.timeout,
        )
    except MexcAuthError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print("MEXC ACCOUNT · AUTHENTICATED READ ONLY")
    print("\nSPOT")
    for item in result["spot"]["balances"]:
        print(
            f"{item['asset']}: total={item['total']} "
            f"(free={item['free']}, locked={item['locked']})"
        )

    print("\nFUTURES")
    for key, value in result["futures"]["balance"].items():
        print(f"{key}: {value}")

    print("\nOrders:      disabled")
    print("Transfers:   disabled")
    print("Withdrawals: disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
