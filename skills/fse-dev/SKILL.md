---
name: fse-dev
description: Execute parallel frontend and backend development using codeagent-wrapper (codex develop agent). Mandatory code review (correctness + simplicity) after every development batch. BLOCKING issues require user decision. MINOR issues are auto-fixed. Produces API documentation on backend completion.
---

# FSE-Dev — Development with Mandatory Code Review

Executes the task graph from `fse-analysis`. All code is written by `codeagent-wrapper` using the `develop` (codex) agent. After every development batch, `code-reviewer` runs in parallel — this step is never skipped.

## Language Requirement

**All user-facing output MUST be in Chinese (Simplified).** This includes all prompts, questions, status banners, error messages, confirmation gates, and progress displays shown to the user. Internal skill instructions may remain in English.

## Hard Constraints

1. **Never write code directly.** All implementation delegated to `codeagent-wrapper --agent develop`. If you find yourself using Edit/Write/MultiEdit tools on project files, STOP and delegate to codeagent-wrapper instead.
2. **Never use the `Agent` tool for development tasks.** The `Agent` tool spawns subagents inside the current Claude Code session and still triggers permission prompts. ALL parallel development MUST be done via `Bash` tool calling `codeagent-wrapper --parallel`. This is the only way to achieve prompt-free parallel execution.
3. **Always prefix develop agent calls with `CODEAGENT_SKIP_PERMISSIONS=true`** to avoid per-file confirmation prompts. Read-only agents (code-reviewer) do NOT need this prefix.
4. **Code review is mandatory** after every batch. No exceptions.
5. **BLOCKING review issues** → present to user: "Fix now / Proceed as-is".
6. **MINOR review issues** → auto-fix via `develop` agent without asking.
7. **Contract is law.** All implementation must match `.fullstack/contracts/openapi.yaml` exactly.
8. If codeagent-wrapper is unavailable → BLOCK, inform user.
9. **All user-facing questions and confirmations MUST use `AskUserQuestion` tool.** Never show text prompts expecting free-form reply.

## Step 0 — Standalone detection (only when invoked directly, not from FSE orchestrator)

If `/fse-dev` is invoked directly by the user (not called by the FSE orchestrator):

1. Check workspace exists:
   ```bash
   python "$HOME/.claude/skills/fse/scripts/workspace.py" status
   ```
   If NOT_FOUND → output: "请先在工作区目录运行 /fse 初始化工作区（执行 fse-init）。" and STOP.

2. Read project paths from workspace:
   ```bash
   python "$HOME/.claude/skills/fse/scripts/workspace.py" get-mode
   ```
   Parse `workspace.json` to get all registered projects and their paths. These are the directories codeagent-wrapper will operate on — do NOT ask the user to provide paths again.

3. If `task-graph.json` does not exist at `.fullstack/tasks/task-graph.json`:
   Use `AskUserQuestion` to collect the task description:
   ```
   没有找到任务图（task-graph.json）。请描述本次开发任务：
   ```
   Then run `fse-analysis` inline to generate the task graph before proceeding to Step 1.

If invoked by FSE orchestrator, skip this step entirely.

## Step 1 — Mark state

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state DEVELOPMENT_IN_PROGRESS
```

```bash
FEATURE_ID=$(python "$HOME/.claude/skills/fse/scripts/workspace.py" get-feature-id 2>/dev/null)
REQ_DIR=".fullstack/requirements/$FEATURE_ID"
ANALYSIS_DIR=".fullstack/analysis/$FEATURE_ID"
CONTRACTS_DIR=".fullstack/contracts/$FEATURE_ID"
```

## Step 2 — Load task graph

Read `.fullstack/tasks/task-graph.json`. Group tasks by execution wave:
- **Wave A**: all tasks with no dependencies (run in parallel)
- **Wave B**: tasks whose dependencies are all in Wave A
- **Wave C**: tasks whose dependencies are all in Wave A or B
- Continue until all tasks are assigned to a wave.

## Step 3 — Execute each wave

> **EXECUTION METHOD (mandatory):** Use the `Bash` tool to call `codeagent-wrapper --parallel`.
> Do NOT use the `Agent` tool. The correct invocation always looks like a `Bash` tool call
> with a heredoc. If you are about to use the `Agent` tool, stop and use the template below instead.

For each wave, run all tasks in parallel using `codeagent-wrapper --parallel`.

### Parallel execution template

```bash
CODEAGENT_SKIP_PERMISSIONS=true codeagent-wrapper --parallel <<'EOF'
---TASK---
id: <task_id>
agent: develop
workdir: <project_path>
---CONTENT---
Implement: <task_name>

Context:
- Requirements: $REQ_DIR/confirmed.md
- API Contract: $CONTRACTS_DIR/openapi.yaml
- Analysis plan: $ANALYSIS_DIR/<project>-plan.md
- Design Spec: $REQ_DIR/design-spec.md (exact visual specs — use these CSS values directly)
- Task: <task description from task-graph>

Implementation rules:
1. Follow ALL patterns found in the existing codebase — do not introduce new conventions.
2. Frontend: match exact endpoint paths/schemas from $CONTRACTS_DIR/openapi.yaml.
   Use mock data only if the backend task is not yet complete (check dependencies).
3. Backend: implement endpoints exactly as specified in $CONTRACTS_DIR/openapi.yaml.
   Include request validation, error handling, and auth checks.
4. Write or update unit tests for every changed module.
5. Frontend: apply exact dimensions, colors, fonts, spacing from design-spec.md (if exists).
   All values are already in the project's configured CSS unit — copy them directly.
   Do NOT approximate colors or round dimension values.
6. Do not modify files outside the scope of this task.

Affected files (from analysis):
<list from task-graph>

---TASK---
id: <task_id_2>
agent: develop
workdir: <project_path_2>
---CONTENT---
...
EOF
```

### Track task status after each wave

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" task-update --id <id> --status completed
```

## Step 4 — Mandatory code review (after EVERY wave)

Run two reviews in parallel immediately after each wave. **Review scope = `git diff` of actual changes**, not vague wave descriptions.

```bash
codeagent-wrapper --parallel <<'EOF'
---TASK---
id: review_quality_wave<N>
agent: code-reviewer
workdir: <primary_project_path>
---CONTENT---
Review the code changes introduced in this wave using `git diff` as the source of truth.

Scope: run `git diff HEAD~1` (or `git diff <base_branch>...HEAD`) to see actual changes.

Evaluate every changed file against:
1. **Project conventions** — check CLAUDE.md (if exists) for explicit rules on imports,
   naming, error handling, logging, testing patterns, and framework conventions.
   Any violation of an explicit project rule is automatically Critical.
2. **Correctness** — logic errors, null/undefined handling, off-by-one, race conditions,
   missing await, incorrect state transitions.
3. **Security (OWASP Top 10 — check only items relevant to this change)**:
   - A01 Broken Access Control (IDOR): can a user access/modify another user's data by changing an ID in the URL/body?
   - A02 Cryptographic Failures: are secrets, tokens, or passwords logged, stored in plaintext, or returned in responses?
   - A03 Injection: is user input concatenated (not parameterized) into SQL queries, OS commands, or log statements?
   - A07 Auth Failures: are there endpoints reachable without authentication/authorization that require it?
   - A10 SSRF: is a user-supplied URL or file path passed to an HTTP client or file reader without allowlist validation?
   Any confirmed vulnerability is automatically Critical (confidence=100).
4. **Contract compliance** — frontend API calls must exactly match $CONTRACTS_DIR/openapi.yaml
   (method, path, request body, response handling). Any mismatch is Critical.
5. **Requirements coverage** — cross-check $REQ_DIR/confirmed.md.
   Flag any acceptance criterion that the code does NOT satisfy.
6. **Edge cases** — empty input, max values, concurrent access, network failure paths.
7. **SOLID principles** — for each modified class or module:
   - S (Single Responsibility): does this class/function do more than one distinct thing?
   - O (Open/Closed): was existing core behavior modified when a new subtype/strategy/extension could have been added instead?
   - D (Dependency Inversion): are high-level modules directly instantiating or importing concrete low-level classes?
   Violations are IMPORTANT issues (confidence ≥ 80 if clearly demonstrated).

Confidence scoring (report ONLY issues scoring ≥ 80):
  100 — Confirmed bug/violation, will definitely cause problems in practice
   80 — Very likely real issue, evidence is strong, not a false positive
  <80 — Do NOT report

Output format:
CRITICAL (confidence ≥ 80, blocks delivery):
- [file:line] confidence=XX | <description> | Fix: <concrete suggestion>

IMPORTANT (confidence ≥ 80, degrades quality):
- [file:line] confidence=XX | <description> | Fix: <concrete suggestion>

If no issues ≥ 80 confidence: output "REVIEW PASSED — no high-confidence issues found."

---TASK---
id: review_simplicity_wave<N>
agent: code-reviewer
workdir: <primary_project_path>
---CONTENT---
Review the code changes from this wave for KISS/YAGNI compliance using `git diff HEAD~1`.

Check only changed files. For each changed file evaluate:
1. Dead code, unused imports, commented-out blocks introduced by this change
2. Unnecessary abstractions or wrappers that add no value
3. Duplicated logic that already exists in the codebase (check existing utilities)
4. Over-engineering — is there a simpler 3-line solution vs a 30-line abstraction?
5. Premature optimization that hurts readability without proven need

Confidence scoring — report ONLY issues scoring ≥ 80:
  100 — Definitely over-engineered / dead code, easy to verify
   80 — Very likely unnecessary complexity

Output format:
SIMPLICITY ISSUES (confidence ≥ 80):
- [file:line] confidence=XX | <description> | Fix: <concrete suggestion>

If no issues ≥ 80: output "SIMPLICITY PASSED."
EOF
```

## Step 5 — Handle review results

Collect all CRITICAL, IMPORTANT, and SIMPLICITY issues from both reviewers.

### If CRITICAL issues exist:

Use `AskUserQuestion`:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
代码审查 — 发现严重问题（阻断交付）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
第 <N> 波发现 <M> 个严重问题：

1. [src/api/user.ts:42] confidence=95 | Missing auth token | Fix: add Authorization header
2. [UserController.java:88] confidence=88 | No null check | Fix: add null guard before DB call

选择处理方式：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
Options: `立即修复（推荐）` / `忽略风险继续`

If "立即修复":
```bash
CODEAGENT_SKIP_PERMISSIONS=true codeagent-wrapper --agent develop - <workdir> <<'EOF'
Fix ONLY the following Critical issues identified in code review.
Do not make any other changes.

<list with file:line, description, and suggested fix>

After fixing, run the relevant tests to verify correctness.
EOF
```
Then re-run Step 4 review on fixed files only. Max 2 fix rounds — if still failing after round 2, escalate to user.

### If IMPORTANT or SIMPLICITY issues only:

Auto-fix without asking user:
```bash
CODEAGENT_SKIP_PERMISSIONS=true codeagent-wrapper --agent develop - <workdir> <<'EOF'
Fix the following non-critical code review issues. Apply only these improvements — no scope creep.

IMPORTANT issues:
<list>

SIMPLICITY issues:
<list>
EOF
```

### If no issues:

Output: `第 <N> 波审查全部通过 ✓`

## Step 6 — Backend API documentation

After all backend tasks complete, generate API docs:

```bash
codeagent-wrapper --agent code-reviewer - <backend_path> <<'EOF'
Generate a complete API integration guide from the implemented endpoints.
Reference: $CONTRACTS_DIR/openapi.yaml

For each endpoint, document:
1. Full URL with base path
2. HTTP method
3. Authentication requirements (header name, token format)
4. Request parameters and body (with field types and constraints)
5. Response structure (success and all error codes)
6. Curl example
7. Frontend JavaScript fetch/axios example

Write the guide to $CONTRACTS_DIR/api-integration-guide.md
EOF
```

## Step 7 — Advance state

After all waves complete and all reviews pass:

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state DEVELOPMENT_DONE
```

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
开发完成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
已完成任务: <N>/<N>
已执行波次: <N>
代码审查: 全部通过
API 文档: $CONTRACTS_DIR/api-integration-guide.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<promise>FSE_PHASE_COMPLETE</promise>
```
