---
name: fse-requirements
description: Gather feature requirements from Lanhu MCP and user description. Apply mandatory first-principles analysis to surface hidden assumptions, conflicts, and boundary conditions before producing a confirmed requirements document (GATE-1). Lite mode uses a compressed inline path.
---

# FSE-Requirements — Requirements Gathering & Confirmation

Fetches requirements from Lanhu MCP, applies a structured first-principles analysis protocol,
produces a requirements document, and blocks on user confirmation (GATE-1).

**First-principles reasoning is the core of this phase.** Stated requirements are treated as
hypotheses, not facts. The analysis must trace every requirement back to bedrock truths before
producing the specification.

## Language Requirement

**All user-facing output MUST be in Chinese (Simplified).** This includes all prompts, questions, status banners, error messages, confirmation gates, and progress displays shown to the user. Internal skill instructions may remain in English.

## Hard Constraints

1. **Lanhu MCP unavailable** → BLOCK immediately:
   ```
   BLOCKED: Lanhu MCP (lanhu) is not responding.
   Please start: D:\mcp-server\lanhu-mcp\start.bat
   Then retry /fse.
   ```
2. **User must explicitly confirm** before state advances.
3. **Conflicts between sources must be surfaced** — never silently pick an interpretation.
4. **Lite mode** skips Lanhu fetch and document generation — see bottom of this file.
5. **All user-facing questions and confirmations MUST use `AskUserQuestion` tool.** Never show text prompts expecting free-form reply.

---

## Standard Path (modes: full, backend, frontend, frontend-ext)

### Step 1 — Mark state

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state REQUIREMENTS_DRAFTING
```

### Step 2 — Collect inputs

Use `AskUserQuestion` to collect these inputs from the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
需求输入
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 蓝湖需求文档 URL：___
2. 蓝湖 UI 设计稿 URL：___
3. 需求描述：___
   （范围、业务背景、约束条件、蓝湖之外的补充信息）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 3 — Fetch from Lanhu MCP (parallel)

Use `lanhu` MCP to simultaneously fetch both URLs:
- **Requirements URL** → extract: page list, functional requirements, interaction flows, business rules, edge cases
- **UI design URL** → extract: page/component inventory, layout structure, all visible text labels,
  field names, button actions, validation messages shown, navigation flows

### Step 3.5 — Extract design specifications (frontend scope only)

If the current mode includes frontend scope AND a UI design URL was provided, extract detailed
visual specifications for frontend development. **Skip this step for backend-only modes.**

#### Phase 1 — Read design config

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" get-design-config
```

This returns `css_unit` (rem or px) and `root_font_size` (e.g. 100).

#### Phase 2 — Get design list and analyze

1. Call `lanhu_get_designs(url)` to get the full list of design images in the project.
2. For each design relevant to this feature (match by name/page from the requirements),
   call `lanhu_get_ai_analyze_design_result(url, design_names=<relevant_names>)`.

#### Phase 3 — Detect DDS Schema failure and supplement

Inspect the response from `lanhu_get_ai_analyze_design_result`. **DDS Schema has failed** if
the response contains ANY of these indicators:
- Text: `"DDS Schema 不可用"` or `"版本数据不存在"`
- Canvas dimensions: `0.0x0.0` or `0x0`
- Empty annotation section (no layer/element data between the annotation markers)

**Regardless of DDS status** (but especially critical when DDS fails), for each relevant design
call `lanhu_get_design_slices(url, design_name)` to get per-element metadata:
- Dimensions and positions (size, position fields)
- Colors (fill, border, text — from metadata)
- Border radius, opacity, shadows
- Image assets with download URLs

#### Phase 4 — Generate design specification document

Using ALL collected data (HTML+CSS from analyze result when DDS succeeded + slice metadata +
design images for visual reference), write `.fullstack/requirements/design-spec.md`:

```markdown
# Design Specification

Generated: <timestamp>
Source: <ui_design_url>
CSS Unit: <css_unit>  |  Root Font Size: <root_font_size>px
Conversion: 1rem = <root_font_size>px (all dimension values below in <css_unit>)

---

## Global Design Tokens

### Colors
| Token | Value | Usage |
|-------|-------|-------|
| primary | rgba(R,G,B,A) | Primary actions, links |
| background | rgba(R,G,B,A) | Page background |

### Typography
| Style | Font Family | Size | Weight | Color |
|-------|-------------|------|--------|-------|
| heading | <font> | <value in css_unit> | <weight> | <rgba> |
| body | <font> | <value in css_unit> | <weight> | <rgba> |

---

## Page: <page_name>

### Artboard
- Size: <width> × <height> (in <css_unit>)

### Component: <component_name>
- Size: width=<val>, height=<val>
- Position: left=<val>, top=<val>
- Background: <rgba color>
- Border: <width> solid <color>
- Border Radius: <val>
- Shadow: <offset-x> <offset-y> <blur> <spread> <color>

#### Text Elements
| Text | Font Size | Font Weight | Color |
|------|-----------|-------------|-------|

#### Child Elements
(nested component specs if applicable)

---
```

**Unit conversion rules:**
- If `css_unit` is `rem`: divide every px dimension value by `root_font_size`, append `rem`.
  Example: `20px` with root_font_size=100 → `0.2rem`
- If `css_unit` is `px`: keep original values, append `px`.
- **Never convert**: colors (rgba), opacity, font-weight, font-family, z-index.

**Data source priority** (highest → lowest):
1. HTML+CSS property values from `lanhu_get_ai_analyze_design_result` (when DDS succeeded and returned real data)
2. Slice metadata from `lanhu_get_design_slices` (always available, primary source when DDS failed)
3. Design images (visual reference for layout relationships only — never guess numeric values from images)

### Step 4 — FIRST-PRINCIPLES ANALYSIS PROTOCOL

This is the mandatory reasoning phase. Execute all five phases in sequence.
Document the output of each phase — it feeds directly into the requirements document.

---

#### PHASE A — Challenge Stated Requirements (5 Whys + WHO/WHEN/WHAT)

**Methodology: 5 Whys** — For every requirement, do not accept the surface statement.
Ask "why does the user need this?" and keep asking until you reach a bedrock business need
(not a UI preference or implementation habit). Minimum 3 levels deep.

```
Example chain:
  Stated: "Add an export button to the user list"
  Why-1:  "So managers can download the list" → Why-2: "To send it to finance monthly"
  Why-3:  "Because finance needs headcount numbers for payroll planning"
  → Real need: scheduled report delivery, not an export button
```

For every requirement extracted from Lanhu and the user description, apply this interrogation:

```
For each requirement R:
  5 WHYS: Ask "why does the user need this?" 3 times. Record the chain.
           Stop when the answer is a verifiable business outcome, not another UI element.
  WHY:   What problem does R solve? (the bedrock answer from the 5 Whys chain)
  WHO:   Which actor triggers R? What permissions must they have?
         (Role, authentication state, ownership of data)
  WHEN:  Under exactly what conditions does R apply?
         (Not just the happy path — what triggers are implied but unstated)
  WHAT:  What data is created, read, updated, or deleted?
         (Name each entity and field explicitly)
  ASSUMPTION CHECK:
         List every assumption this requirement makes.
         Mark each as VERIFIED (stated explicitly) or ASSUMED (implied/inferred).
```

Flag any requirement where WHY cannot be answered from the source material — these are
high-risk misunderstandings that must be resolved before development begins.

---

#### PHASE B — Decompose to Bedrock Truths

Strip away everything that is UI, framework, or convention. Find only the irreducible facts:

**Data truths:**
- What entities exist? What are their mandatory fields (minimum, not exhaustive)?
- What relationships exist between entities? (one-to-many, ownership, etc.)
- What uniqueness or integrity constraints must hold?

**State truths:**
- What states can each entity be in?
- What triggers state transitions?
- What states are terminal (cannot go back)?

**Permission truths:**
- Who is allowed to perform each operation? (role/ownership/conditions)
- What happens when an unauthorized user attempts an operation?

**Business invariants:**
- What rules must ALWAYS be true, regardless of how the UI is implemented?
- (e.g. "An order total can never be negative", "A user can only belong to one org")

Write these as falsifiable statements, not vague prose.

---

#### PHASE C — Rebuild Specification from Truths

Starting ONLY from the verified bedrock truths in Phase B, derive what the system must do.

```
For each bedrock truth T:
  → What API operations are needed to satisfy T?
  → What UI state or interaction is the minimum to expose T to the user?
  → Is the stated requirement consistent with T, or does it add unnecessary complexity?
```

**Contrast with stated requirements:**
- Does the Lanhu spec require MORE than what the truths demand? → Flag as potential over-engineering
- Does it require LESS than the truths demand? → Flag as a gap (missing requirement)
- Forbidden conclusion: "assume they meant X" — surface every mismatch explicitly

---

#### PHASE D — Cross-Validate Sources

Compare: Lanhu requirements doc vs. Lanhu UI design vs. user description.

For each discrepancy found, produce a conflict record:

```
CONFLICT-001
  Source A: Lanhu requirements says "Users can delete their own comments"
  Source B: Lanhu UI design shows no delete button on comments
  Source C: User description does not mention comment deletion
  Impact: BLOCKING — cannot implement without knowing the correct behavior
  Resolution needed: Which source is correct?
```

Classification:
- **BLOCKING**: implementation cannot proceed without resolution
- **MINOR**: can proceed with a reasonable default, but user should confirm

---

#### PHASE E — Hidden Requirement Discovery (Boundary Inventory)

**Methodology: Boundary Inventory** — Every requirement has a set of unstated boundaries.
This phase forces systematic enumeration of those boundaries BEFORE development begins,
so they become explicit requirements rather than runtime surprises.

Systematically probe scenarios not shown in the happy path:

| Boundary | Questions to answer |
|----------|---------------------|
| **Empty state** | What does the UI show when there is no data? Is this specified? |
| **Error state** | What error messages appear for each failure mode? Exact copy/text? |
| **Permission boundary** | What does a lower-privilege user see on restricted pages/actions? |
| **Data limits** | Are there max lengths, max counts, file size limits? Exact numbers? |
| **Null / zero / negative** | What happens with empty string, 0, null, or negative values on key fields? |
| **Concurrent access** | What if two users modify the same record simultaneously? Who wins? |
| **Network failure** | What happens if an API call fails mid-operation? Is partial state possible? |
| **Success feedback** | How does the user know the operation succeeded? (toast/redirect/refresh) |
| **Idempotency** | What happens if the user submits the same form twice in quick succession? |
| **Time boundaries** | Are there date/time constraints? Timezone handling? Expiry scenarios? |

For each scenario: either find the answer in source material, or mark as OPEN QUESTION.
OPEN QUESTION items with HIGH impact must be resolved at GATE-1 before proceeding.

---

### Step 5 — Write requirements document

Write `.fullstack/requirements/raw.md`:

```markdown
# Feature Requirements: <feature_name>

Generated: <timestamp>  |  Workspace: <workspace_id>  |  Mode: <mode>

## Sources
- Requirements URL: <url or "n/a">
- UI Design URL: <url or "n/a">
- User Description: <summary>

---

## First-Principles Analysis Summary

### Bedrock Truths (Phase B output)
**Entities**: <list with fields>
**State machine**: <entity → states → transitions>
**Permissions**: <who can do what>
**Business invariants**: <always-true rules>

### Source Conflicts (Phase D output)
| ID | Source A | Source B | Impact | Resolution |
|----|----------|----------|--------|------------|
| CONFLICT-001 | ... | ... | BLOCKING | Pending user decision |

### Open Questions (Phase E output)
| ID | Scenario | Impact |
|----|----------|--------|
| Q-001 | Empty state not specified | MINOR |

---

## Confirmed Requirements

### FR-001: <title>
**Derived from**: <bedrock truth(s) from Phase B>
**Why**: <root problem this solves — Phase A WHY>
**Who**: <actor + required permission>
**What**: <exact CRUD operation on exact entity/field>
**Acceptance Criteria**:
- [ ] Given <precondition>, when <action>, then <observable result>
- [ ] Error case: given <invalid state>, when <action>, then <error message shown>

---

## UI Requirements

### Pages / Components
| Component | Route | Purpose | Empty State | Error State |
|-----------|-------|---------|-------------|-------------|

---

## Out of Scope
- <explicit exclusion>

## Non-Functional Requirements
- Performance: ...
- Compatibility: ...
- Accessibility: ...
```

### Step 5.5 — Generate BDD Test Cases

Generate `.fullstack/tests/test-cases.md` — the pre-built test baseline consumed by `fse-test`.
This step runs after `raw.md` is written so test cases reflect all Phase A–E findings.

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Generate a structured BDD test case file from the requirements analysis.

Input: .fullstack/requirements/raw.md
       (Pay attention to: Bedrock Truths, State machines, Permission truths, Boundary Inventory findings)

For every FR, produce a MINIMUM of three test cases:

TC-<FR_ID>-01 (Happy Path):
  fr_ref: <FR-xxx>
  type: happy_path
  priority: P0
  Given: <initial system state and auth role>
  When:  <action the user performs>
  Then:  <observable result — what changes, what is displayed, what is returned>

TC-<FR_ID>-02 (Sad Path — error or permission rejection):
  fr_ref: <FR-xxx>
  type: sad_path
  priority: P0
  Given: <invalid precondition — wrong role / missing required data / invalid input>
  When:  <same or similar action>
  Then:  <expected rejection — specific error message / redirect / element hidden>

TC-<FR_ID>-03 (Boundary — BVA):
  fr_ref: <FR-xxx>
  type: boundary
  priority: P1
  target_field: <field name and its constraint, e.g. "title: 1–100 chars">
  cases:
    - value: <min-1>  → expected: reject with "<specific error text>"
    - value: <min>    → expected: accept
    - value: <max>    → expected: accept
    - value: <max+1>  → expected: reject with "<specific error text>"

Cross-feature test cases (add EACH that applies to this feature):

TC-STATE-001 (State Transition — add if any stateful entity exists):
  type: state_transition
  priority: P0
  entity: <entity name>
  valid_transition: <from_state> → <to_state> via <action> → expected: success
  invalid_transition: <from_state> → <to_state> (illegal) → expected: error

TC-PERM-001 (Permission Boundary — add for every role-restricted action):
  type: permission
  priority: P0
  action: <the restricted operation>
  case_no_auth: unauthenticated request → expected: 401 or login redirect
  case_wrong_role: lower-privilege user → expected: 403 or action hidden
  case_wrong_owner: user A accesses user B's resource → expected: 403

TC-CONC-001 (Concurrency — add if simultaneous writes are possible):
  type: concurrency
  priority: P1
  scenario: two users submit the same form simultaneously
  expected: exactly one succeeds, other receives clear error (not silent data corruption)

Write the complete output to .fullstack/tests/test-cases.md.
Include a summary table at the top:

| TC ID | FR Ref | Type | Priority | Description |
|-------|--------|------|----------|-------------|
EOF
```

### Step 6 — Confirmation Gate (GATE-1)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GATE-1：需求确认
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[requirements document content]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
未解决冲突: <N>  |  待确认问题: <N>

If conflicts exist, use `AskUserQuestion` to present each BLOCKING conflict:
  "CONFLICT-001: [description] — 哪个解释是正确的？"
  Wait for user decision, update document, then present final document for confirmation.

Use `AskUserQuestion` to ask:
  1. 确认 — 需求准确完整，进入分析阶段
  2. 修改 — 提供反馈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**If "确认"** (and all BLOCKING conflicts resolved):
```bash
cp .fullstack/requirements/raw.md .fullstack/requirements/confirmed.md
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state REQUIREMENTS_CONFIRMED
```
Output: `<promise>FSE_PHASE_COMPLETE</promise>` — 需求已确认

**If "修改"**: apply feedback, re-run relevant analysis phases, re-present.

---

## Lite Path (mode: lite)

When mode is `lite`, skip Lanhu fetch, skip document generation, skip GATE-1.

Ask inline using `AskUserQuestion`:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
精简模式 — 快速需求收集
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
描述本次改动（具体到文件、组件、行为）:
  ___

完成后应该达成什么效果（当前不满足的）?
  ___

有什么约束条件，或者哪些东西不能改?
  ___
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Apply Phase A (WHY/WHO/WHEN/WHAT) inline — just ask: "Why is this change needed? Who triggers it?"
Write a 5-10 line summary to `.fullstack/requirements/confirmed.md` (no full doc).
Advance state directly to `REQUIREMENTS_CONFIRMED`. No user gate.
