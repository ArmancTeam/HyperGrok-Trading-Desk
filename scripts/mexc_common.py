#!/usr/bin/env python3
"""MEXC public market-data transport. GET only; no credentials or trading."""

import json
import re
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = "https://api.mexc.com"
DEFAULT_TIMEOUT = 10
MAX_RESPONSE_BYTES = 2_000_000


class MexcPublicError(RuntimeError):
    """A public MEXC request or response failed validation."""


def validate_symbol(symbol, futures=False):
    if not isinstance(symbol, str):
        raise MexcPublicError("symbol must be text")

    symbol = symbol.strip().upper()
    pattern = r"[A-Z0-9]{2,20}_[A-Z0-9]{2,20}" if futures else r"[A-Z0-9]{2,30}"

    if not re.fullmatch(pattern, symbol):
        raise MexcPublicError("invalid market symbol")

    return symbol


def public_get(path, params=None, timeout=DEFAULT_TIMEOUT):
    """Perform an HTTPS GET against the fixed MEXC public API host."""
    if not isinstance(path, str) or not path.startswith("/"):
        raise MexcPublicError("invalid API path")

    if "://" in path or path.startswith("//") or ".." in path or "\\" in path:
        raise MexcPublicError("unsafe API path")

    if not isinstance(timeout, (int, float)) or not 1 <= timeout <= 30:
        raise MexcPublicError("timeout must be between 1 and 30 seconds")

    params = params or {}
    if not isinstance(params, dict):
        raise MexcPublicError("params must be an object")

    query = urllib.parse.urlencode(params)
    url = BASE_URL + path + (("?" + query) if query else "")

    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "HyperGrok-Desk/1.0"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise MexcPublicError(f"MEXC returned HTTP {response.status}")

            raw = response.read(MAX_RESPONSE_BYTES + 1)

        if len(raw) > MAX_RESPONSE_BYTES:
            raise MexcPublicError("MEXC response exceeds size limit")

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MexcPublicError("MEXC returned invalid JSON") from exc

        if isinstance(payload, dict):
            code = payload.get("code")
            if code is not None and str(code) not in ("0", "200"):
                raise MexcPublicError(
                    f"MEXC API error: {payload.get('msg', code)}"
                )

        return payload

    except urllib.error.HTTPError as exc:
        raise MexcPublicError(f"MEXC HTTP error: {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise MexcPublicError(f"MEXC connection error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise MexcPublicError("MEXC request timed out") from exc


def require_object(payload, label="response"):
    if not isinstance(payload, dict):
        raise MexcPublicError(f"{label} must be a JSON object")
    return payload


def require_list(payload, label="response"):
    if not isinstance(payload, list):
        raise MexcPublicError(f"{label} must be a JSON list")
    return payload
