#!/usr/bin/env python3
"""Offline fail-closed provenance and quote sanity checks; no network or trading."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

@dataclass(frozen=True)
class QualityResult:
    status: str
    accepted: bool
    reasons: tuple
    source: str | None
    symbol: str | None
    market_type: str | None
    observed_at: str | None
    age_seconds: float | None
    def to_dict(self):
        d = asdict(self)
        d["reasons"] = list(self.reasons)
        return d

def _time(value):
    if not isinstance(value, str): return None
    try: dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: return None
    if dt.tzinfo is None: return None
    return dt.astimezone(timezone.utc)

def _positive(value):
    try: d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError): return None
    return d if d.is_finite() and d > 0 else None

def validate_snapshot(snapshot, *, now=None, max_age_seconds=30,
                      expected_source=None, expected_market_type=None):
    """Validate normalized {source,symbol,market_type,observed_at,bid,ask,last}."""
    if not isinstance(snapshot, dict): snapshot = {}
    reasons = []
    source, symbol, kind = snapshot.get("source"), snapshot.get("symbol"), snapshot.get("market_type")
    if not isinstance(source, str) or not source.strip(): reasons.append("missing_source")
    if not isinstance(symbol, str) or not symbol.strip(): reasons.append("missing_symbol")
    if kind not in ("spot", "perpetual"): reasons.append("invalid_market_type")
    if expected_source and source != expected_source: reasons.append("source_mismatch")
    if expected_market_type and kind != expected_market_type: reasons.append("market_type_mismatch")
    observed = _time(snapshot.get("observed_at"))
    if observed is None: reasons.append("invalid_or_missing_timestamp")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None: raise ValueError("now must be timezone-aware")
    age = None
    if observed:
        age = (current.astimezone(timezone.utc) - observed).total_seconds()
        if age < -2: reasons.append("timestamp_in_future")
        elif age > max_age_seconds: reasons.append("stale_data")
    bid, ask, last = (_positive(snapshot.get(k)) for k in ("bid", "ask", "last"))
    if bid is None: reasons.append("invalid_bid")
    if ask is None: reasons.append("invalid_ask")
    if last is None: reasons.append("invalid_last")
    if bid is not None and ask is not None and bid >= ask: reasons.append("crossed_or_locked_book")
    if bid is not None and ask is not None and last is not None and bid < ask:
        mid = (bid + ask) / 2
        if last > mid * Decimal("1.25") or last < mid * Decimal("0.75"):
            reasons.append("last_price_outlier")
    ok = not reasons
    return QualityResult("PASS" if ok else "REJECT", ok, tuple(reasons),
        source if isinstance(source, str) else None,
        symbol if isinstance(symbol, str) else None,
        kind if isinstance(kind, str) else None,
        observed.isoformat().replace("+00:00", "Z") if observed else None,
        round(age, 3) if age is not None else None)

def require_accepted(result):
    if not result.accepted:
        raise ValueError("market data rejected: " + ", ".join(result.reasons))
