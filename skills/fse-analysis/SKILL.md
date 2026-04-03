---
name: fse-analysis
description: Parallel codebase analysis filtered by mode scope. Applies first-principles validation to verify that the confirmed requirements are implementable and internally consistent before producing implementation plans. Confirms with user (GATE-2). Lite mode uses a compressed file-list-only path.
---

# FSE-Analysis — Project Analysis & Implementation Planning

Analyzes each in-scope project against confirmed requirements. Uses first-principles validation
to catch mismatches between requirements and reality before any code is written.

## Language Requirement

**All user-facing output MUST be in Chinese (Simplified).** This includes all prompts, questions, status banners, error messages, confirmation gates, and progress displays shown to the user. Internal skill instructions may remain in English.

## Hard Constraints

1. **Read scope from workspace** — only analyze projects matching `current_feature.scope`.
2. **Read confirmed requirements** — never plan from unconfirmed inputs.
3. **First-principles validation**: after analysis, verify the plan is grounded in bedrock truths.
4. If codeagent-wrapper unavailable → BLOCK.
5. **All user-facing questions and confirmations MUST use `AskUserQuestion` tool.** Never show text prompts expecting free-form reply.
6. **Never use the `Agent` tool.** All parallel codebase analysis MUST be done via `Bash` tool calling `codeagent-wrapper --parallel`. The `Agent` tool runs inside the main session and does not provide isolation.

## Step 1 — Mark state and read scope

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state ANALYSIS_IN_PROGRESS
python "$HOME/.claude/skills/fse/scripts/workspace.py" get-mode
```

Read `current_feature.scope` from `workspace.json`. Only analyze projects whose type is in scope:
- `backend` in scope → analyze all registered backend projects
- `frontend` in scope → analyze all registered frontend projects

## Step 2 — Parallel project analysis (scope-filtered)

Build one codeagent task per in-scope project. Run all simultaneously:

```bash
codeagent-wrapper --parallel <<'EOF'
---TASK---
id: analysis_<type>_<name>
agent: code-explorer
workdir: <project_path>
---CONTENT---
Analyze this <frontend|backend> project against the confirmed requirements below.

Requirements: .fullstack/requirements/confirmed.md
Design Spec: .fullstack/requirements/design-spec.md (if exists — contains exact dimensions,
colors, fonts, spacing in the project's configured CSS unit. Use these values directly in
component implementations. Do NOT approximate — every value is extracted from the design tool.)

Your analysis must be grounded in first-principles — not in what is convenient to implement,
but in what the requirements actually demand at a bedrock level.

Produce:

1. AFFECTED FILES
   List every file to create or modify. For each: path, action (CREATE/MODIFY), reason.
   Reason must reference a specific requirement ID (FR-xxx), not a vague description.

2. <If frontend> NEW COMPONENTS
   Name, purpose, props/emits, which FR it satisfies.
   For each component, reference the matching section in design-spec.md (if exists).
   Include the exact dimensions, colors, and spacing values from the spec.

2.5 <If frontend> DESIGN SPEC MAPPING
   For each component in section 2, map it to the corresponding section in design-spec.md.
   List the exact CSS properties (dimensions, colors, spacing, typography) that must be applied.
   Flag any component where the design spec is missing or incomplete.

3. <If frontend> API CALLS REQUIRED
   Every backend endpoint this frontend will consume.
   Format: METHOD /path — what data is sent — what is expected back
   Flag any endpoint not yet defined in the API surface.

4. <If backend> NEW ENDPOINTS
   METHOD /path — request schema — response schema — auth required — FR it satisfies

5. <If backend> DATABASE CHANGES
   New tables, columns, indexes. Include DDL SQL for each.

6. IMPLEMENTATION TASKS
   Ordered list. For each task:
     - ID: FE-001 or BE-001
     - Name: imperative verb phrase
     - Files: (list)
     - Dependencies: (task IDs that must complete first, or "none")
     - Parallelizable: YES / NO
     - Complexity: Low / Medium / High

7. FIRST-PRINCIPLES CHECK
   For each implementation task, answer:
   - Which bedrock truth (from requirements Phase B) does this task satisfy?
   - Is there a simpler way to satisfy the same truth?
   - Does this task do MORE than the truth requires? (flag as potential over-engineering)

8. FMEA LITE (Failure Mode and Effects Analysis)
   For every new service / controller / component being introduced:
   - Most likely failure mode: what breaks if this component crashes or returns wrong data?
   - Impact: HIGH (data loss/corruption or security breach) / MEDIUM (feature unavailable) / LOW (degraded UX)
   - Required mitigation: what error handling / fallback / retry logic is needed?
   List only HIGH and MEDIUM impact items. LOW items may be omitted.

9. CONCURRENCY ANALYSIS
   For every write operation (create / update / delete):
   - Can two simultaneous requests conflict on the same record or resource?
   - What mechanism prevents data corruption? (DB unique constraint / optimistic lock / pessimistic lock / idempotency key)
   - Does the frontend need duplicate-submission prevention? (loading state / debounce / disabled button after click)
   Flag any write operation with no concurrency protection as HIGH RISK.

10. STATE MACHINE VALIDATION (apply only if the feature includes stateful entities)
    For each stateful entity (e.g. order, application, approval):
    - List all valid states
    - List all valid transitions (from_state → to_state, trigger action)
    - List illegal transitions that MUST be explicitly rejected (e.g. COMPLETED → PENDING is not allowed)
    - Verify that implementation tasks include guards/checks for illegal transitions

---TASK---
id: analysis_<type>_<name2>
...
EOF
```

## Step 3 — Download Lanhu UI assets and verify design spec (frontend scope only)

After frontend analysis, extract asset requirements from the analysis output.
Use `lanhu` MCP to download each identified asset:
- UI screenshots → `.fullstack/assets/screenshots/<page>.png`
- Icons → `.fullstack/assets/icons/<name>.svg`

**Verify design spec coverage:**
- Check if `.fullstack/requirements/design-spec.md` exists (generated during requirements phase).
- If it exists, verify it covers all pages/components identified in the analysis output.
- If any page/component is missing from the spec, log a warning:
  `WARN: design-spec.md 缺少以下页面/组件的设计规格：<list>. 开发时将依赖截图参考。`

## Step 4 — First-principles validation pass

After all analysis tasks complete, run a cross-project validation:

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Perform a first-principles validation of the analysis results.

Inputs:
- Confirmed requirements: .fullstack/requirements/confirmed.md
  (Pay special attention to the "Bedrock Truths" and "Business Invariants" sections)
- Frontend analysis: .fullstack/analysis/frontend-<name>.md (if exists)
- Backend analysis:  .fullstack/analysis/backend-<name>.md (if exists)

Answer each question with evidence:

1. COMPLETENESS: Does the combined task list satisfy EVERY requirement in confirmed.md?
   List any FR-xxx that has no corresponding implementation task. These are GAPS.

2. OVER-ENGINEERING: Does any task implement more than its FR requires?
   List tasks where the scope exceeds the bedrock truth. These are candidates for pruning.

3. INTERFACE CONSISTENCY: Do frontend API calls match backend endpoints exactly?
   List any mismatch (endpoint path, HTTP method, request/response schema differences).
   These must be resolved before writing a single line of code.

4. DEPENDENCY VALIDITY: Are task dependencies correctly ordered?
   Identify any circular dependencies or missing sequential constraints.

5. RISK FLAGS: What is the highest-risk implementation decision in this plan?
   Which bedrock truth is hardest to satisfy with the proposed approach?

6. FMEA COVERAGE: Are all HIGH-impact failure modes (from individual project analyses) covered by a
   corresponding error handling or fallback task?
   List any HIGH-impact failure mode that has no implementation task addressing it. FAIL if any found.

7. CONCURRENCY COVERAGE: Do all write operations have an explicit concurrency protection mechanism?
   List any write path identified in the analyses that has no protection. WARN if any found.

Output a VALIDATION REPORT with PASS / WARN / FAIL per check.
FAIL on any check → must be resolved before GATE-2.
EOF
```

## Step 5 — Write implementation plan documents

Write per-project plans to `.fullstack/analysis/<type>-<name>.md` (one per project).

Also write API surface outline to `.fullstack/analysis/api-surface.md` (backend scope only):

```markdown
# API Surface Outline

## Endpoints Required by This Feature

| Method | Path | Auth | Request | Response | FR |
|--------|------|------|---------|----------|----|
| GET | /api/users | Bearer | query: page,size | PageResult<User> | FR-001 |
```

## Step 6 — Build task dependency graph

Consolidate all tasks into `.fullstack/tasks/task-graph.json`:

```json
{
  "mode": "<mode>",
  "scope": ["frontend", "backend"],
  "tasks": [
    {
      "id": "BE-001",
      "name": "Implement user query endpoint",
      "project": "<backend_name>",
      "type": "backend",
      "workdir": "<backend_path>",
      "fr_ref": "FR-001",
      "complexity": "medium",
      "depends_on": [],
      "can_parallel": true,
      "status": "pending"
    },
    {
      "id": "FE-001",
      "name": "User list page",
      "project": "<frontend_name>",
      "type": "frontend",
      "workdir": "<frontend_path>",
      "fr_ref": "FR-001",
      "complexity": "medium",
      "depends_on": ["BE-001"],
      "can_parallel": false,
      "status": "pending"
    }
  ]
}
```

## Step 7 — Confirmation Gate (GATE-2)

**必须使用 `AskUserQuestion` 工具** 向用户展示以下确认信息并获取回复：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GATE-2：实现方案确认
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
范围：<frontend|backend|both>
任务：共 <N> 项（<M> 项可并行）
验证：<PASS|N 警告|N 失败>

[如有失败项，必须先展示并要求解决，然后再呈现方案]

任务执行波次：
  波次 A（并行）：BE-001, BE-002, FE-001
  波次 B（A 之后）：FE-002（依赖 BE-001）

发现缺口：<N>  |  过度工程标记：<N>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
完整方案：.fullstack/analysis/
验证报告：.fullstack/analysis/validation-report.md

  1. 确认 — 继续
  2. 修改 — 提供反馈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**如用户选择"确认"**（且验证无失败项）：
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state ANALYSIS_CONFIRMED
```
输出：`<promise>FSE_PHASE_COMPLETE</promise>`

---

## Lite Path (mode: lite)

When mode is `lite`, skip the full analysis and validation pass. Run one fast task:

```bash
codeagent-wrapper --agent code-explorer - <primary_workdir> <<'EOF'
Quick analysis for a small change.

Requirements summary: .fullstack/requirements/confirmed.md

Identify:
1. AFFECTED FILES — exact list (path + why, ≤8 files expected for lite mode)
2. CHANGE SUMMARY — one paragraph describing the minimal change set
3. RISKS — any non-obvious side effects of this change

If affected files exceed 8, flag: "这可能超出 lite 任务的范围——请考虑使用完整模式。"
EOF
```

Write result to `.fullstack/analysis/lite-plan.md`. Advance state to `ANALYSIS_CONFIRMED` immediately.
Lite 模式无需用户确认门控。
