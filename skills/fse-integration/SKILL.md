---
name: fse-integration
description: Integration testing phase. For own-backend modes (full, frontend): starts backend with pre-flight checks, connects frontend to real APIs, fixes issues immediately. For frontend-ext mode: connects frontend to external backend using stored integration target. Loops until clean or max rounds exceeded.
---

# FSE-Integration — Integration Testing (联调)

Connects frontend to real backend APIs. Two paths depending on `integration_target.type`:
- **own**: start the backend yourself, then integrate
- **external**: backend is provided by an external team — connect directly using stored URL + auth

## Language Requirement

**All user-facing output MUST be in Chinese (Simplified).** This includes all prompts, questions, status banners, error messages, confirmation gates, and progress displays shown to the user. Internal skill instructions may remain in English.

## Hard Constraints

1. **Pre-flight checks must pass** before any backend startup attempt (own mode).
2. **Every issue gets a severity**: BLOCKING (stops integration) or MINOR (log and continue).
3. **Backend fixes are immediate** — issue found → fix in same round.
4. **Max rounds: 5.** Exceeding → escalate to user.
5. **backend mode skips this phase entirely** — routed directly to fse-test.
6. **All user-facing questions and confirmations MUST use `AskUserQuestion` tool.** Never show text prompts expecting free-form reply.

## Step 1 — Mark state and read integration target

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state INTEGRATION_IN_PROGRESS
python "$HOME/.claude/skills/fse/scripts/workspace.py" get-mode
```

Read `current_feature.integration_target` from `workspace.json`:
- `type: own` → proceed to Step 2 (pre-flight + startup)
- `type: external` → skip to **External Backend Path** section

---

## Own Backend Path (modes: full, frontend)

### Step 2 — Pre-flight checks

For each backend project, run pre-flight before startup:

```bash
codeagent-wrapper --agent code-explorer - <backend_path> <<'EOF'
Pre-flight integration readiness check:

1. PORT: Is port <port> free? (netstat -ano | findstr :<port>)
2. ENV VARS: Are all required vars from .fullstack/tasks/manual-checklist.md present?
3. DATABASE: Can the configured datasource connect? Run a test query.
4. BUILD: Does the project compile without errors?
   (mvn compile -q / gradle compileJava / python -m py_compile / tsc --noEmit)

Report each as: PASS or FAIL: <reason>
If ANY fails → report all failures, do not proceed.
EOF
```

**If any FAIL:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
预检失败 — 无法启动后端
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✗ Database: connection refused
  ✗ Port 8080: in use (PID 12345)

请解决以上问题后重新执行 /fse。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
BLOCK — do not continue.

### Step 3 — Start backend service(s)

Read `startup_args`, `startup_env`, and `health_check_url` from `workspace.json`.

```bash
codeagent-wrapper --agent develop - <backend_path> <<'EOF'
Start the backend development server.

Start command  : <start_cmd> <startup_args>
Environment    : <KEY=VALUE pairs from startup_env>
Expected port  : <port>
Health check   : <health_check_url, or "port-open check" if empty>

Steps:
1. Export all environment variables
2. Run the full start command in the background
3. Wait up to 90 seconds:
   - If health_check_url set: poll until HTTP 200
   - If empty: check port <port> is accepting connections
4. On failure: capture last 80 lines of output and report

Note: If Nacos registration is required, wait for the "Registration successful" log line.

Report: STARTED (port <port>) or FAILED: <error summary>
EOF
```

If startup FAILS → BLOCK, display captured error log.

### Step 4 — Integration round loop (own backend)

Proceed to **Round Loop** section below.

---

## External Backend Path (mode: frontend-ext)

### Step 2ext — Verify external backend reachability

```bash
codeagent-wrapper --agent code-explorer - <frontend_path> <<'EOF'
Verify the external backend is reachable before integration.

Base URL : <integration_target.base_url>
Auth type: <integration_target.auth_type>
Auth value: <masked — use from workspace.json>

Steps:
1. Call: GET <base_url>/health or <base_url>/ping or the first endpoint in the API docs
2. Apply the auth header/cookie as configured
3. Verify: HTTP 200 received and response is valid JSON

If unreachable: report exact error (DNS, connection refused, auth failure, etc.)

Report: REACHABLE or UNREACHABLE: <reason>
EOF
```

If UNREACHABLE → BLOCK, report error. User must fix credentials/URL.

### Step 3ext — Load external API docs

Determine API docs source from `integration_target`:

**If `api_docs_url` is set**: use `lanhu` MCP or direct fetch to load the Swagger/OpenAPI spec.
**If `api_docs_path` is set**: read the local file.
**If neither**: ask user to paste the API documentation inline.

Write the loaded API docs to `.fullstack/contracts/external-api-docs.md` for reference.

### Step 4ext — Integration round loop (external backend)

Proceed to **Round Loop** section below, substituting:
- Backend base URL = `integration_target.base_url`
- Auth = `integration_target.auth_type` + `integration_target.auth_value`
- API reference = `.fullstack/contracts/external-api-docs.md`
- **No backend fix cycle** — if an external API doesn't behave as documented, log the issue
  and notify the user. Do not attempt to fix code you don't own.

---

## Round Loop (shared by both paths)

Run up to `max_rounds` (5) rounds.

### Frontend integration check

```bash
codeagent-wrapper --agent develop - <frontend_path> <<'EOF'
Connect frontend to real backend APIs and verify each endpoint.

Backend base URL: <base_url>
Auth: <type + value>
API reference: .fullstack/contracts/openapi.yaml (own) OR
               .fullstack/contracts/external-api-docs.md (external)

For each endpoint referenced in frontend code:
1. Switch from mock data to real API call (if not already done)
2. Call the endpoint with realistic test data
3. Verify:
   - HTTP status matches expected
   - Response schema matches contract
   - Data renders correctly in the UI component

For each problem found, report:
ISSUE: <description>
ENDPOINT: <METHOD /path>
EXPECTED: <per contract>
ACTUAL: <what the API returned>
SEVERITY: BLOCKING | MINOR
EOF
```

### Issue handling

For each BLOCKING issue:

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" add-issue \
  --phase integration --text "<description>" --severity blocking
```

**Own backend** → fix immediately on backend:
```bash
codeagent-wrapper --agent develop - <backend_path> <<'EOF'
Fix this integration issue:
Issue: <description>
Endpoint: <METHOD /path>
Expected (per contract): <expected>
Actual: <returned>

Fix the implementation to match .fullstack/contracts/openapi.yaml.
Do not change the contract.
EOF
```

Then mandatory code review on the backend fix:
```bash
codeagent-wrapper --agent code-reviewer - <backend_path> <<'EOF'
Review the fix for: <issue description>
1. Fix correctly resolves the issue
2. No regression introduced
3. Response now matches .fullstack/contracts/openapi.yaml exactly
Classify new issues as BLOCKING or MINOR.
EOF
```

**Frontend fix** — if the issue requires a frontend-side change (e.g., request format, data mapping, error handling):
```bash
codeagent-wrapper --agent develop - <frontend_path> <<'EOF'
Fix this frontend integration issue:
Issue: <description>
Endpoint: <METHOD /path>
Expected (per contract): <expected>
Actual (frontend behavior): <observed>

Adjust frontend code to match .fullstack/contracts/openapi.yaml.
Do not change the contract.
EOF
```

Then mandatory code review on the frontend fix:
```bash
codeagent-wrapper --agent code-reviewer - <frontend_path> <<'EOF'
Review the frontend fix for: <issue description>
1. Fix correctly resolves the issue
2. No regression introduced
3. Request/response handling matches .fullstack/contracts/openapi.yaml exactly
4. UI rendering remains correct after the change
Classify new issues as BLOCKING or MINOR.
EOF
```

**External backend** → log issue, notify user:
```
发现外部 API 问题（无法修复 — 非我方代码）：
  问题: <description>
  接口: <METHOD /path>
  需要的操作: 联系 API 提供方，或调整前端以适配该响应。
```

### Round clean check

- All BLOCKING issues resolved → round clean
- Increment round counter
- If clean → exit loop
- If not clean and rounds < 5 → next round
- If round 5 not clean → escalate

### Max rounds exceeded

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
联调 — 超出最大轮次（5/5）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
未解决的阻断性问题：
<list>

  1. 继续 — 增加轮次
  2. 人工介入 — 手动审查并提供指导
  3. 中止 — 回到开发阶段
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Use `AskUserQuestion` tool** for this escalation.

## Step 5 — Integration passed

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state INTEGRATION_PASSED
```

Output:
```
联调通过 — <N> 轮，<M> 个问题已解决
<promise>FSE_PHASE_COMPLETE</promise>
```
