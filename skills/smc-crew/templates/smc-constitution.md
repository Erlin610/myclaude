# SMC-Crew Constitution — Immutable Rules

> Authorized by Founder. No role may modify the Absolute tier. Versioned tier may be updated by Strategist with backtest evidence and PM approval only.

---

## Capital Rules (Absolute — never change)

- Initial capital: 100 USDT
- Max isolated margin per trade: 5 USDT (hard cap, enforced at code level)
- Max loss per trade including fees: ≤ 5 USDT
- Leverage: **200x (fixed)**
- Pyramiding (adding to positions) is not allowed

## Position Sizing Rule (Absolute — derived from above)

Position size is calculated dynamically from the stop distance of each trade:

```
position_size = min(
    max_risk_usd / stop_distance_usd_per_eth,   ← risk constraint
    (max_margin_usd × leverage) / entry_price    ← margin constraint
)

where:
  max_risk_usd   = 5 USDT
  max_margin_usd = 5 USDT
  leverage       = 200
  stop_distance  = |entry_price - stop_price|  (in USDT per ETH)
```

Example: entry = 2100, stop = 2090 (10-point stop)
- Risk constraint:   5 / 10 = 0.500 ETH
- Margin constraint: (5 × 200) / 2100 = 0.476 ETH
- Actual position:   min(0.500, 0.476) = **0.476 ETH**
- Margin used:       (0.476 × 2100) / 200 = 5.0 USDT ✓
- Max loss at stop:  0.476 × 10 = 4.76 USDT ✓

The binding constraint (smaller of the two) always applies. Code must enforce both.

## Profit Targets (Acceptance Criteria — Absolute)

| Level | Weekly Profit | Monthly Profit |
|-------|--------------|----------------|
| Minimum | 50 USDT | 200 USDT |
| Ideal | 100 USDT | 400 USDT |

## Strategy Rules (Absolute)

- Instrument: ETH/USDT Perpetual Contract
- Methodology: SMC (Smart Money Concepts) / ICT
- Backtest data: Must cover at least 1 full year
- Backtest must simulate fees and slippage

## Quality Gates — Tier 1: Absolute

These cannot be changed regardless of backtest results:

- Max loss per trade (including fees) > 5 USDT → BLOCK (capital safety)
- Margin per trade > 5 USDT → BLOCK (capital safety)
- Stop-loss has no SMC structural basis → BLOCK (discipline rule)
- Backtest data span < 1 year → BLOCK (insufficient evidence) — Phase B only. Phase A (6–8 week fast iteration) is explicitly exempt.

## Quality Gates — Tier 2: Versioned

These are initial priors. Strategist may propose updated thresholds at the start of each major version, backed by evidence from completed backtests, subject to PM approval. Current values:

| Threshold | Current Value | Last Updated |
|-----------|--------------|--------------|
| Min win rate | 40% | v0 (initial) |
| Min risk/reward | 1.5 | v0 (initial) |
| Max drawdown | 40% | v0 (initial) |

> To update: Strategist proposes new value with evidence → PM approves → update this table → RiskGuard reads updated table.

## Growth Rules

- After every backtest, all roles MUST complete HTRU-U (knowledge update) — no exceptions
- Shared knowledge base (knowledge/shared/) is updated first; role-specific knowledge is derived from it
- graveyard.md blocks specific failed configurations, not entire directions. The same direction may be retried with a different angle.

## Expert Independence Rule

- SMC-Strategist (claude backend) and SMC-Engineer (codex backend) must produce independent outputs
- They must use different model backends — this is by design to ensure genuine adversarial validation
- Merging them into a single role is prohibited

## Termination Condition

This system is a pure backtest optimization system. Live execution is handled by a separate system.
When strategy passes all acceptance criteria, the crew packages and delivers to Founder for live system integration.
