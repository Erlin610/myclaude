# HTRU Cycle — Team Growth Methodology

HTRU is the core growth engine of SMC-Crew. It must be executed in full after every backtest. Skipping any phase is not allowed.

```
H — Hypothesize
T — Test
R — Reflect
U — Update
```

---

## H — Hypothesize

**Owner**: SMC-Strategist (leads), SMC-Engineer (validates feasibility)

**Output standard**: Every hypothesis must meet this format. Vague directions are not accepted.

```markdown
## Hypothesis H-<id>
- Statement: [One sentence, must be falsifiable by backtest]
- Parameters:
  - Direction timeframe: [e.g., 4H]
  - Direction condition: [e.g., BOS confirmed on 4H close]
  - Entry timeframe: [e.g., 15m]
  - Entry trigger: [e.g., CHoCH + OB retest]
  - Stop loss: [e.g., below OB low + buffer; buffer is a hypothesis parameter — no fixed % here]
  - Take profit: [e.g., next BSL / SL distance × 2.5]
  - Session filter: [e.g., UTC 07:00-16:00 only]
  - Leverage: 200x (fixed, from constitution — not a variable parameter)
- Expected outcomes:
  - Win rate: ≥ X%
  - Risk/reward: ≥ Y
  - Avg trades/week: ~N
  - Estimated weekly profit: ~$Z
- Theoretical basis: [Specific ICT/SMC principle — no vague "may work" statements]
- Difference from graveyard: [Explicitly state how this differs from falsified directions]
- Engineering feasibility request: [Ask Engineer to confirm this can be backtested without bias]
- Status: pending
```

**Hypothesis status machine**:
```
pending → testing → validated  (enters strategist/knowledge.md validated section)
                 → falsified   (enters graveyard.md with Breakthrough angle)
                 → partial     (close current H-N, spawn H-N+1 as revised version, H-N+1 status = pending)
```
Note: PARTIAL does not enter graveyard. The original hypothesis is closed with status=partial and cross-referenced from H-N+1.

---

## T — Test

**Owner**: SMC-Developer (implements), SMC-Reviewer (audits), SMC-RiskGuard (validates), backtest engine (executes)

**Test protocol (designed by Engineer, defined per hypothesis)**:

```markdown
## Test Protocol T-<hypothesis-id>
- Backtest range: [start date ~ end date]
- In-sample data: [80% for backtest]
- Out-of-sample data: [20% for validation — only examined AFTER in-sample results]
- Data granularity: [e.g., 15m candles]
- Fee settings: Maker 0.02%, Taker 0.05%
- Slippage: 0.05% (conservative estimate)
- Isolated margin simulation: each position independent, liquidation does not affect others
- Exclusion conditions: [e.g., 2h before/after major macro events]
```

---

## R — Reflect

**Owner**: All roles, independent reflection then consolidated

**Required questions — no skipping allowed**:

### Strategist Reflection
1. Did backtest results match my expectations? Where did they diverge?
2. Do failed trades share common characteristics? (session? market structure?)
3. Were winning trades due to strategy edge or randomness?
4. What does this result update in my understanding of ETH?
5. Where was my hypothesis wrong? Wrong premise or wrong parameters?
6. What is the most valuable next hypothesis to test?

### Engineer Reflection
1. Is the backtest trustworthy? Any undetected bias?
2. Is in-sample vs out-of-sample degradation within acceptable range (< 30%)?
3. Are trades evenly distributed across the test period, or clustered in one market regime?
4. Changing key parameters by ±10%: does performance collapse? (yes = overfitting risk)
5. What architectural improvements should be made next iteration?

### Developer Reflection
1. What implementation problems were encountered?
2. Which code patterns are worth reusing?
3. Any unhandled edge cases or bugs?

### Reviewer Reflection
1. What new problem patterns were found in this audit?
2. Which new checks should be added to the standard checklist?

---

## U — Update

**Execution order**: Shared knowledge base FIRST, then role-specific knowledge derived from it.

### Step 1: Update shared knowledge base

All roles contribute. PM coordinates.

```
knowledge/shared/eth-instrument.md    ← ETH instrument characteristics (evidence-gated, see threshold below)
knowledge/shared/market-facts.md      ← general validated facts
knowledge/shared/failure-patterns.md  ← failure patterns
knowledge/shared/breakthroughs.md     ← breakthroughs (if any)
```

**ETH instrument update is evidence-gated, not mandatory.**

Strategist asks: "Is there enough evidence this iteration to record an ETH characteristic?"
The answer is frequently "no, not yet" — and that is correct.

Record only when ALL conditions are met:
- Sample ≥ 30 trades exhibiting the pattern
- Pattern observed across at least 2 different market regimes (not just one trend run)
- The observation is specific and measurable (not "ETH is volatile")

If threshold not met: do not record. Note the observation in `research-agenda.md` as a question to watch.

Format:
```markdown
## [MF-<id>] ETH Fact: <title>
- Content: <specific fact>
- Source: H-<id>, Iteration #<N>
- Confidence: high/medium (based on X trade sample)
- Validated period: <date range>
```

### Step 2: Each role derives role-specific knowledge

Each role reads the updated shared knowledge and extracts what is relevant to their domain:

```
knowledge/strategist/hypotheses.md      ← update hypothesis statuses
knowledge/strategist/smc-knowledge.md   ← update SMC application insights
knowledge/strategist/research-agenda.md ← update open questions
knowledge/engineer/backtest-patterns.md ← update trusted backtest patterns
knowledge/engineer/bias-blacklist.md    ← update bias blacklist
knowledge/developer/code-patterns.md   ← update effective code patterns
knowledge/developer/bug-rootcauses.md  ← record bug root causes
knowledge/reviewer/audit-checklist.md  ← update audit checklist
```

### Step 3: Update graveyard.md (if hypothesis was falsified)

**What goes in graveyard: the specific configuration that failed, not the direction.**

```markdown
## G-<id>: <specific configuration title>
- Hypothesis ID: H-<N>
- Test iteration: #<N>
- What specifically failed: [exact parameters that were tested]
- Why it failed: [root cause — market structure reason, not just "metrics were bad"]
- What this does NOT rule out: [adjacent angles in the same direction that remain open]
- Breakthrough angle: [if the core idea may still have merit, what different approach is worth trying]
```

**graveyard blocks the specific failed configuration, not the direction family.**
Strategist can return to the same strategic direction with a different angle.
Only close a direction entirely after 3+ distinct configurations all fail with the same root cause.

### Step 4: PM updates compass.md and mission.json

Update current state, next action, and knowledge entry counts.
