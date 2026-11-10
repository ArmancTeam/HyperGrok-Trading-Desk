#!/usr/bin/env python3
"""MEXC authenticated read-only GET transport."""

import hashlib
import hmac
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import time

SPOT_BASE_URL = "https://api.mexc.com"
FUTURES_BASE_URL = "https://contract.mexc.com"
DEFAULT_TIMEOUT = 10
MAX_RESPONSE_BYTES = 2_000_000


class MexcAuthError(RuntimeError):
    """Authenticated MEXC read request failed."""


def _validate_credentials(api_key, api_secret):
    if not isinstance(api_key, str) or not api_key.strip():
        raise MexcAuthError("API key is missing")
    if not isinstance(api_secret, str) or not api_secret:
        raise MexcAuthError("API secret is missing")


def _validate_path(path):
    if (
        not isinstance(path, str)
        or not path.startswith("/")
        or "://" in path
        or path.startswith("//")
        or ".." in path
        or "\\" in path
    ):
        raise MexcAuthError("invalid API path")


def _encode_params(params):
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise MexcAuthError("params must be an object")

    for key, value in params.items():
        if not isinstance(key, str) or not isinstance(
            value, (str, int, float)
        ):
            raise MexcAuthError("invalid query parameter")

    return urllib.parse.urlencode(params)


def _request_json(url, headers, timeout):
    if not isinstance(timeout, (int, float)) or not 1 <= timeout <= 30:
        raise MexcAuthError("timeout must be between 1 and 30 seconds")

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "HyperGrok-Desk/1.0",
            **headers,
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise MexcAuthError(
                    f"MEXC returned HTTP {response.status}"
                )
            raw = response.read(MAX_RESPONSE_BYTES + 1)

        if len(raw) > MAX_RESPONSE_BYTES:
            raise MexcAuthError("MEXC response exceeds size limit")

        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MexcAuthError("MEXC returned invalid JSON") from exc

    except urllib.error.HTTPError as exc:
        raise MexcAuthError(
            f"MEXC HTTP error: {exc.code}"
        ) from exc
    except urllib.error.URLError as exc:
        raise MexcAuthError("MEXC connection error") from exc
    except TimeoutError as exc:
        raise MexcAuthError("MEXC request timed out") from exc


def signed_spot_get(
    path, params, api_key, api_secret,
    timeout=DEFAULT_TIMEOUT, timestamp_ms=None
):
    """MEXC Spot HMAC-SHA256 signed GET."""
    _validate_credentials(api_key, api_secret)
    _validate_path(path)

    query_params = dict(params or {})
    if "signature" in query_params or "timestamp" in query_params:
        raise MexcAuthError("reserved query parameter")

    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)

    query_params["timestamp"] = timestamp_ms
    query = _encode_params(query_params)

    signature = hmac.new(
        api_secret.encode("utf-8"),
        query.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    url = (
        SPOT_BASE_URL + path + "?" + query
        + "&signature=" + signature
    )

    return _request_json(
        url,
        {"X-MEXC-APIKEY": api_key},
        timeout,
    )


def signed_futures_get(
    path, params, api_key, api_secret,
    timeout=DEFAULT_TIMEOUT, timestamp_ms=None
):
    """MEXC Futures HMAC-SHA256 signed GET."""
    _validate_credentials(api_key, api_secret)
    _validate_path(path)

    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)

    query = _encode_params(
        dict(sorted((params or {}).items()))
    )

    signature_payload = api_key + str(timestamp_ms) + query
    signature = hmac.new(
        api_secret.encode("utf-8"),
        signature_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    url = FUTURES_BASE_URL + path
    if query:
        url += "?" + query

    return _request_json(
        url,
        {
            "ApiKey": api_key,
            "Request-Time": str(timestamp_ms),
            "Signature": signature,
        },
        timeout,
    )
