# User-requested trading-desk integration and current status

This document is an integration map and status ledger. It does **not** prove that every
feature reported as successful in Grok exists in this repository or is running in the
Grok environment. The source archive remains the upstream HyperGrok v1.7.1 project plus
the local additions listed below. Grok's remote workspace was not accessible from this ZIP
update, so no remote code or runtime state has been synchronized.

## Non-negotiable operating boundaries

- Hyperliquid Perpetual and MEXC Spot are separate products and must never be conflated.
- Hyperliquid and MEXC public market data may be read; this ZIP does not establish a live
  MEXC adapter or prove a connected feed.
- Binance is excluded and disabled in the reference configuration.
- Real orders are disabled: `LIVE_TRADING_ENABLED=false`,
  `LIVE_ORDER_EXECUTION=false`, and `real_orders_enabled=false`.
- Automatic real-order execution remains disabled. User preference for automated
  execution is recorded as a future preference only; it is not authorization to trade.
- Paper Trading and Shadow Trading are simulation-only. Never use real funds or send
  exchange orders during these modes.
- MEXC starting capital is undecided; do not assume or initialize a real balance.
- Never put API keys, secrets, private keys, or withdrawal credentials in reports or chat.
- Missing, stale, mismatched, or unsourced data must block downstream decisions.
- Daily report preference: 08:00 Europe/Istanbul. Runtime scheduling and successful
  delivery remain unverified. Weekly reports are not requested.

## User-reported build inventory

The user reported completing these setup prompts in Grok. This list records the user's
reports, not independent proof of implementation or runtime health:

### Market data, research and analysis

- Hyperliquid Perpetual market-data integration.
- MEXC Spot public market-data integration.
- Arbitrage scanner and advanced arbitrage analysis.
- Market alerts, AI Signal Engine, backtesting and dashboard.
- Health Monitor, Security Audit, Whale Tracker and Smart Money Tracker.
- Strategy Optimizer, Market Regime Detector and Multi-Timeframe Analysis.
- Portfolio & Correlation Manager and Liquidity & Order Flow Analyzer.
- Funding Rate & Liquidation Monitor, News & Sentiment Intelligence.
- AI Decision Engine, Adaptive Learning Engine and Opportunity Ranking.
- Trade Journal & Performance Intelligence, Command Center and Autonomous Research Agent.
- Data Quality & Provenance Guard.

### Risk, simulation and execution preparation

- Risk Guardian and Paper Trading configuration.
- MEXC live-order infrastructure preparation, connection/security checks and approval gate.
- Final pre-live security audit.
- Autonomous Trading Engine restricted to Paper/Shadow modes.
- Autonomous stress tests, strategy optimization and AI decision validation.
- MEXC Shadow Trading Engine and performance evaluation.
- A 100-trade validation module and subsequent performance audit.
- MEXC autonomous market watch, operational status audit and self-healing/recovery prompt.
- Production-readiness review and consolidated final audit prompt.
- 24-hour Shadow Observation start/status checks.
- 100-trade performance audit and independent raw-record consistency audit.
- Final stable-baseline/backup prompt.

The user reported `PASS` for the 24-hour observation validation, the 100-trade
performance audit, and the independent consistency audit, and reported 100 completed
Shadow trades. The underlying logs, timestamps, raw trade records, metrics and backup
artifact were not supplied with this ZIP. Treat those outcomes as **user-reported, not
independently verified**. In particular, the 100-trade count and 24-hour runtime cannot be
confirmed from this archive.

## Reference paper limits

- Virtual equity: 10,000 USDT.
- Risk per trade: 50 USDT (0.5%).
- Daily loss stop: 100 USDT (1%).
- Aggregate open risk: 150 USDT (1.5%).
- Minimum reward/risk: 1:2.
- Pause after 3 consecutive losses.

These are reference limits, not evidence that a running application enforces them.
See `config/trading-desk.example.json`.

## What is actually present in this ZIP

- Upstream HyperGrok v1.7.1 repository content: role profiles, skills, read-only
  Hyperliquid utilities and related documentation.
- `scripts/data_quality_guard.py`: offline validation of normalized quote records,
  including source, symbol, market type, freshness, positive bid/ask/last, crossed books
  and gross last-price outliers. `require_accepted(result)` provides a fail-closed helper.
- `scripts/test_data_quality_guard.py`: eight unit tests for the validator.
- `config/trading-desk.example.json`: reference-only configuration for the requested
  Hyperliquid/MEXC split, disabled Binance, paper-only mode, risk limits, daily-report
  preference and data-quality policy.
- `docs/USER_REPORTED_CHANGELOG.md`: chronological record of later user-reported setup
  milestones and verification limitations.

The following were **not found as concrete runtime implementations** in the inspected
archive: a connected MEXC adapter, the custom paper broker, signal/arbitrage engines,
custom dashboard and trackers, autonomous decision pipeline, Shadow Trading runtime,
24-hour scheduler/worker, persistent 100-trade ledger, recovery worker, and daily report
scheduler. Their completion in Grok may exist separately, but it was not transferred or
verified here. The local Data Quality Guard is offline and is not wired to live feeds.

## Validation performed for this archive

- Data Quality Guard unit tests: 8 passed in the earlier local validation.
- ZIP archive integrity: passed for the prior archive; the newly generated archive is
  checked again when this update is packaged.
- Full project test suite: previously **NOT TESTED** because the run hit a 60-second
  execution limit. Do not describe the full suite as passed unless it is rerun to completion.

## Next verification work (do not add features before this)

1. Compare this ZIP with the latest Grok workspace export or Git commit; import actual
   source changes rather than relying on prompt-completion messages.
2. Obtain the 24-hour observation logs and 100 raw Shadow trade records, including unique
   IDs, timestamps, entry/exit prices, costs and net P&L; independently recompute metrics.
3. Verify MEXC Spot and Hyperliquid Perpetual source metadata and product separation.
4. Confirm risk limits are enforced in executable code and fail closed on missing data.
5. Verify the 08:00 Europe/Istanbul daily schedule with an actual successful run.
6. Verify backup creation and restore integrity, not just that a backup prompt completed.
7. Keep live order routes disabled and Binance excluded.
