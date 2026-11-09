# User-reported setup changelog

Date recorded: 2026-11-09 (Europe/Istanbul)

This file consolidates the setup milestones the user reported completing in Grok. It is a
history of reported prompt outcomes, not a repository commit log and not independent proof
that each feature exists in the runtime.

## Reported milestones

1. Hyperliquid Perpetual and MEXC Spot market-data setup; Binance intentionally excluded.
2. Market scanning, alerts, signal analysis, backtesting, dashboard, monitoring,
   security review, whale/smart-money tracking, market-regime and multi-timeframe analysis.
3. Portfolio/correlation, order-flow, funding/liquidation, news/sentiment, AI decision,
   adaptive learning, opportunity ranking, journal, command center and research-agent
   setup prompts.
4. Data-quality/provenance guard and operational health/recovery prompts.
5. Risk Guardian and Paper Trading limits: 10,000 USDT virtual equity; 50 USDT risk per
   trade; 100 USDT daily loss stop; 150 USDT aggregate open risk; minimum 1:2 reward/risk;
   pause after three consecutive losses.
6. MEXC execution infrastructure preparation, security checks and approval-gate prompts.
7. Autonomous execution prompts explicitly restricted to Paper/Shadow modes; live execution
   remained disabled.
8. MEXC Shadow Trading setup, stress/strategy/AI validation and 100-trade validation.
9. User-reported result: 100 Shadow trades; user then reported PASS for the performance
   audit and independent record-consistency audit. Raw records and calculated values were
   not included in the ZIP supplied for this update.
10. User-reported PASS for the 24-hour Shadow Observation validation. No timestamps or
    durable worker logs were supplied, so elapsed time and background continuity remain
    unverified here.
11. Final stable-baseline and backup prompt reported completed. The backup output itself
    was not supplied, so its existence and restore integrity remain unverified here.

## Current safety settings and preferences

- `LIVE_TRADING_ENABLED=false`
- `LIVE_ORDER_EXECUTION=false`
- `real_orders_enabled=false`
- Automated real orders: disabled, despite the user's future preference for automation.
- Paper Trading and Shadow Trading only.
- Hyperliquid Perpetual and MEXC Spot remain distinct.
- Binance: do not add; disabled.
- MEXC initial capital: undecided; no real capital amount should be assumed.
- Daily report preference: 08:00 Europe/Istanbul; actual scheduler/run not verified.
- Weekly report: not requested.

## Evidence still needed

- Latest Grok repository export or commit containing the changes made in Grok.
- Raw 100-trade ledger and 24-hour observation logs.
- Actual performance metrics and reproducible calculation output.
- A real backup file plus successful restore test.
- A successful daily-report scheduler execution record.

Until those are provided, use the labels **user-reported** or **not independently verified**.
Do not treat a Grok prompt returning “Başarılı” as proof of runtime implementation.
