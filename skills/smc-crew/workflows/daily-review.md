# Daily Review Workflow

Triggered when Founder provides new market data. Run via `/smc-crew review`.

---

## Trigger Conditions

Founder provides any of:
- Today's ETH candle data (any timeframe)
- Today's market event summary
- Live trading screenshots or data files

---

## Execution Flow

### Step 1: PM receives data

PM reads compass.md to confirm current state, then forwards data to Strategist.

### Step 2: Strategist performs market reflection

```bash
CODEAGENT_SKIP_PERMISSIONS=true codeagent-wrapper --backend <strategist_backend> - smc-crew/knowledge/strategist <<'PROMPT'
[Inject roles/strategist.md full content]
[Inject knowledge/shared/ all content]
[Inject knowledge/strategist/ all content]
[Inject board.md IMMUTABLE ZONE]

## Daily Review Task

Today's market data:
<data provided by Founder>

Answer the following questions:
1. What is today's market structure? (4H view: trend / consolidation / reversal)
2. Based on current strategy (<current strategy version>), how many entry opportunities existed today? Where?
3. Did actual price action validate or invalidate the current strategy hypothesis?
4. Were there any SMC signals that occurred but the current strategy did not capture?
5. Does this review trigger a new hypothesis or revision of an existing one?

Output format:
- Market analysis (concise)
- Strategy validation verdict: CONFIRM / QUESTION / FALSIFY
- New insights (if any)
- New hypothesis triggered (if any — use HTRU-H format)
- Content to add to shared knowledge base (if any)
PROMPT
```

### Step 3: PM decides whether to trigger new HTRU cycle

```
Strategist output = CONFIRM      → log to evolution-log.md, no new iteration
Strategist output = QUESTION     → log + add to research-agenda, accumulate
Strategist output = FALSIFY      → update graveyard.md + trigger new hypothesis immediately
New hypothesis with high confidence → trigger full HTRU cycle
```

### Step 4: Update knowledge base

Regardless of verdict, valid review content gets recorded:
- `knowledge/shared/market-facts.md` (new instrument observations)
- `knowledge/strategist/research-agenda.md` (open questions)
- `evolution-log.md` (append today's review record)

### Step 5: PM updates compass.md

Record today's review conclusion and next action.

---

## Accumulation Trigger Rule

When the following condition is met, automatically trigger a new full HTRU cycle:

```
Any question in research-agenda has accumulated ≥ 3 QUESTION evidence entries
  → Strategist now has sufficient data to form a new hypothesis
  → PM schedules new hypothesis into HTRU-H phase
```
