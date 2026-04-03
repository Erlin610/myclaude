---
name: fse-test
description: Functional testing skill. Works both integrated in the FSE pipeline and as a fully standalone tool for QA team members. Builds a Navigation Map from the frontend project so Playwright tests navigate by known paths (never exploring blindly). Three test case sources — pre-generated from requirements, derived from Lanhu design, or manual user input. API testing (curl) for backend mode, browser flow testing (Playwright MCP) for frontend/full mode. Defects trigger fix + code review cycle (max 3 rounds).
---

# FSE-Test — Functional Testing

Two execution contexts:
- **Pipeline mode**: called by FSE orchestrator after development. Workspace exists, `test-cases.md` may be pre-generated, navigation map may exist. Skip straight to testing.
- **Standalone mode**: invoked directly with `/fse-test` by any team member. No prior FSE run required. Collects project paths, credentials, mode, and test case source from scratch.

## Language Requirement

**All user-facing output MUST be in Chinese (Simplified).** Internal skill instructions may remain in English.

## Hard Constraints

1. **Tests derive from real sources** — every test traces to a confirmed requirement, a Lanhu flow, or an explicit user-described scenario. Never fabricate scenarios.
2. **Playwright MCP required for browser mode** — if unavailable, BLOCK immediately.
3. **Navigation Map required for browser mode** — never run Playwright tests without a map. A test agent without a map is a new employee on their first day, clicking around randomly.
4. **Fix cycle always includes code review** — same quality gate as `fse-dev`.
5. **Max fix rounds: 3.** After that, escalate to user.
6. **All user-facing questions MUST use `AskUserQuestion` tool.**
7. **NEVER tell the user to manually start services.** When services are DOWN in a local environment, the skill MUST use `workspace.py start-services` to start them automatically after confirmation. Printing "请手动启动" or "请先启动项目" is FORBIDDEN. If auto-start fails after two retries, THEN ask the user for help.
8. **NEVER ask the user which port a service runs on.** All ports are registered in workspace.json. Use `list-projects` to read them. If a port is missing from workspace.json, ask once and save it — do not ask on every run.

---

## Step 0 — Context Detection and Setup

### 0A — Detect execution context

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" status 2>/dev/null
```

**FOUND** → **Pipeline mode**: workspace and project paths are already configured.
  - Skip to Step 0C (credentials check).
  - Read mode from workspace: `python "$HOME/.claude/skills/fse/scripts/workspace.py" get-mode`

**NOT_FOUND** → **Standalone mode**: continue with Step 0B.

---

### 0B — Standalone Setup (skip if pipeline mode)

#### Collect project paths

Use `AskUserQuestion`:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FSE-Test 独立模式 — 项目路径
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
前端项目绝对路径（如 D:/projects/my-frontend）:
  留空则跳过浏览器流程测试
后端项目绝对路径（如 D:/projects/my-backend）:
  留空则跳过接口测试
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Initialize minimal workspace:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" init "$(pwd)"
```

Register provided paths (detect tech stack inline via quick file check):
```bash
# For each provided project path:
python "$HOME/.claude/skills/fse/scripts/workspace.py" add-project \
  --type <frontend|backend> --name <dirname> --path "<path>" --tech <detected>
```

#### Choose test mode

Use `AskUserQuestion`:
```
选择测试类型:
  1. 接口测试 (API) — HTTP 请求验证后端接口
  2. 页面流程测试 (Browser) — 浏览器模拟用户操作
  3. 两者都测
```

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-mode <backend|frontend|full>
```

#### Choose test case source

Use `AskUserQuestion`:
```
测试用例来源:
  1. 已有文件 — 使用 .fullstack/tests/test-cases.md（由 fse-requirements 生成）
  2. 蓝湖设计稿 — 提供蓝湖 URL，AI 自动分析需求/设计稿生成用例
  3. 手动描述 — 直接描述要测试的业务场景，AI 结构化为用例
```

Store choice; used in Step 2.

---

### 0C — Environment Selection and Account Setup (both modes)

#### Check configured environments

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" list-test-envs
```

**Pipeline mode**: automatically use `local` environment — set it active, then verify `base_url` is populated. Never ask the user what port to use.

```bash
# Ensure local env exists with a base_url derived from the frontend project port
python "$HOME/.claude/skills/fse/scripts/workspace.py" list-projects --type frontend
```

Parse the first frontend project's `port` field (e.g. `9527`). Then:

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" get-test-env --name local 2>/dev/null
```

- If `base_url` is already non-empty → use it as-is.
- If `base_url` is empty or env does not exist → auto-set from the frontend project port:

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-test-env \
  --name local --base-url "http://localhost:<frontend_port>" --type local
```

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-active-test-env --name local
```

> **Rule**: Do NOT ask the user "which port?". The port is already registered in workspace.json from fse-init. If no frontend project is registered, ask once for the base URL via `AskUserQuestion` then save it.

**Standalone mode**: if environments already configured, present them via `AskUserQuestion`:
```
选择测试环境:
  <list each: name (type) — base_url>
  ➕ 配置新环境
```

If "配置新环境" OR no environments exist, collect via `AskUserQuestion`:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
配置测试环境
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
环境名称（如 local / dev / staging）: ___
应用基础地址（如 http://localhost:3000）: ___
环境类型:
  1. 本地 (localhost) — 失败时自动修复代码后重测
  2. 远程 (dev/staging) — 失败时生成 Bug 报告，不自动改代码
TAPD 项目 ID（远程环境填写，留空跳过）: ___
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-test-env \
  --name "<name>" --base-url "<url>" --type <local|remote> [--tapd-project-id "<id>"]
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-active-test-env --name "<name>"
```

#### Configure accounts for active environment

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" get-test-env
```

If no accounts configured, collect via `AskUserQuestion` (multiple roles supported):
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测试账号配置（支持多个角色）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
角色1 名称（如 admin）: ___  用户名: ___  密码: ___
角色2 名称（如 teacher，留空结束）: ___  用户名: ___  密码: ___
角色3（留空结束）: ___
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

For each role provided:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" add-test-account \
  --role "<role>" --username "<username>" --password "<password>"
```

---

### 0D — Service Check and Account Validation (both modes)

#### Check all registered services

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" check-services
ENV_TYPE=$(python "$HOME/.claude/skills/fse/scripts/workspace.py" get-test-env | grep "^type:" | awk '{print $2}')
```

**If all services are UP** → proceed to account validation.

**If any service is DOWN and `ENV_TYPE=remote`**:
```
❌ 远程环境服务不可达：<name>（端口 <port>）
请确认服务已部署并运行后重试。
```
BLOCK.

**If any service is DOWN and `ENV_TYPE=local` (or unset)**:

Use `AskUserQuestion`:
```
检测到以下服务未运行：
  • <name>（前端/后端）  端口: <port>  启动命令: <start_cmd>
  • ...

请手动启动上述服务，启动完成后选择继续。
  1. 已启动，继续测试
  2. 停止测试
```

After user selects option 1, re-scan:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" check-services
```

- All UP → proceed to testing (Step 1).
- Still DOWN → repeat `AskUserQuestion` (show which are still DOWN).

> **Account credentials are NOT pre-validated.** Skip straight to testing.
> If a test fails at the login step, record it as a credential failure and use `AskUserQuestion`:
> ```
> 账号登录失败：role=<role>
> 请检查账号信息是否正确，然后选择：
>   1. 更新账号后重试
>   2. 跳过此角色的测试
>   3. 停止测试
> ```
> Then update via: `workspace.py add-test-account --role <role> --username <u> --password <p>`

---

## Step 1 — Navigation Map (browser mode only; skip for API-only)

### Why this step exists

A Navigation Map is a structured document that tells the test agent:
- **WHERE** each feature lives: menu path, exact route URL
- **WHAT** is on each page: buttons (exact text), form fields (label + constraints)
- **HOW** to navigate there: step-by-step from login

Without it, Playwright starts each test as a new user who has never seen the app —
spending tokens exploring menus, guessing selectors, failing on renamed buttons.
With it, every step is pre-resolved before execution begins.

### 1A — Check existence and freshness

```bash
test -f .fullstack/testing/navigation-map.md && echo "EXISTS" || echo "MISSING"
```

**If MISSING**: generate immediately (Step 1B). No prompt needed.

**If EXISTS**: check staleness against frontend git history:
```bash
MAP_DATE=$(grep "^Generated:" .fullstack/testing/navigation-map.md | head -1 | sed 's/Generated: //')
git -C <frontend_path> log --since="$MAP_DATE" --oneline \
  -- src/router/ src/components/Sidebar* src/components/Nav* src/layout/ 2>/dev/null | head -3
```

- No output → map is **FRESH** → skip to Step 2.
- Has output → map is **STALE** → print:
  ```
  导航地图检测到前端路由/导航变更（自 <MAP_DATE>），正在更新导航地图…
  ```
  Then proceed to Step 1B.

### 1B — Generate Navigation Map

```bash
codeagent-wrapper --agent code-explorer - <frontend_path> <<'EOF'
Generate a Navigation Map for this frontend application.

PURPOSE: This document is used as context by a Playwright test agent so it can navigate
the app by known paths instead of exploring from scratch on every test run. Be specific
and concrete — every piece of information must be verifiable in the source code.

STEP 1 — Router Analysis
Find and read the router definition file(s): src/router/index.ts, src/router/routes.ts,
or equivalent. For each route extract:
  - Full URL path (resolve nested routes to their complete paths)
  - Component file path (relative)
  - Meta: requiresAuth, roles/permissions, page title if present
Build a complete flat route table.

STEP 2 — Menu / Navigation Structure
Find navigation components by searching for: Sidebar, NavMenu, AppMenu, SideMenu, Menu
in src/components/, src/layout/, src/views/layout/.
Extract the COMPLETE menu tree:
  - Top-level menu items: display text (keep Chinese), route or click action
  - Sub-menu items: display text (keep Chinese), route
Map: "Chinese menu text" → exact route path

STEP 3 — Page Component Analysis (top 20 routes by importance)
Priority order: list/index pages > create/edit form pages > detail pages > others.
For each priority page, read its component and extract:
  - Form fields: el-form-item label (Chinese), v-model binding, required, maxlength/max/min
  - Buttons: display text (Chinese), @click target (router push path, or submit/save action)
  - Table columns: column labels (for verify step in tests)
  - Select/dropdown options: option labels (Chinese)

STEP 4 — Business Flow Reconstruction
For each logical module (group by route prefix or menu section), write the standard flows:
  CREATE: menu path → list page → create button → form fields → submit → verify
  EDIT: list page → row action "编辑" → form → submit → verify
  DELETE: list page → row action "删除" → confirm dialog → verify
  VIEW: list page → row click → detail page

OUTPUT: Write to .fullstack/testing/navigation-map.md using this EXACT structure:

---
# Navigation Map

Generated: <current ISO-8601 datetime, e.g. 2025-01-15T10:30:00>
Frontend: <absolute path to frontend project>
Router file: <relative path>
Git commit: <output of: git rev-parse HEAD>

---

## Information Architecture

### Module: <Chinese module name>
Menu path: <左侧导航 → X → Y>
Base route: /xxx

#### Page: <Chinese page name>
Route: /xxx/yyy
Component: src/views/xxx/yyy.vue
Auth required: yes | no | role:<role_name>

Key elements:
| Element | Type | Label / Text | Constraint | Action / Binding |
|---------|------|-------------|------------|------------------|
| 创建按钮 | Button | "创建XXX" | — | router.push('/xxx/create') |
| 名称 | Input | "名称" | required, maxlength=50 | v-model: form.name |
| 状态 | Select | "状态" | options: 启用/禁用 | v-model: form.status |

---

## Business Flows

### Flow: 创建<业务对象>
Precondition: logged in as <admin|user>
Steps:
  1. Navigate: <base_url>/login → fill username/password → click "登录"
  2. Click: sidebar item "<exact Chinese text>"
  3. Click: submenu item "<exact Chinese text>"
  4. Current URL: <base_url>/xxx/list
  5. Click: button "<exact Chinese button text>"
  6. Current URL: <base_url>/xxx/create
  7. Fill: field "<label>" = "<example valid value>"
  8. Click: button "<submit button text>"
  9. Verify: redirected to <base_url>/xxx/list, new row with "<value>" visible in table

### Flow: 编辑<业务对象>
...

---

## Route Quick Reference
| Module | Page | Route | Auth | Component |
|--------|------|-------|------|-----------|
EOF
```

Output to user:
```
导航地图已生成（<N> 个模块，<N> 条业务流程）
```

### 1C — Supplement with Lanhu (optional — only if Lanhu URL was provided)

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Supplement the navigation map with Lanhu design information.

Existing map: .fullstack/testing/navigation-map.md
Lanhu URL: <url>

Steps:
1. Fetch Lanhu content via lanhu MCP (requirements doc + UI designs)
2. For each business flow shown in Lanhu:
   - If the flow already exists in the map: verify consistency, update if Lanhu is more specific
   - If the flow is missing from the map: add it
3. Add any field constraints visible in the design (e.g. placeholder text showing expected format)
4. Do NOT remove information confirmed by code analysis — supplement only

Update .fullstack/testing/navigation-map.md in place.
EOF
```

---

## Step 2 — Test Cases

### 2A — Pre-generated file (pipeline default OR standalone source choice 1)

```bash
test -f .fullstack/tests/test-cases.md && echo "FOUND" || echo "MISSING"
```

If FOUND:
```
已加载测试用例文件：<N> 条用例（.fullstack/tests/test-cases.md）
```
Skip to Step 3.

If MISSING and pipeline mode: warn and fall through to generate from requirements:
```
未找到预生成测试用例，将从 confirmed.md 实时生成。
```

Then run the BDD generation prompt from fse-requirements Step 5.5 inline, writing to `.fullstack/tests/test-cases.md`.

### 2B — Generate from Lanhu (standalone source choice 2)

Collect Lanhu URL via `AskUserQuestion` if not already provided in Step 1C.

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Generate BDD test cases from a Lanhu design.

Inputs:
- Fetch Lanhu content via lanhu MCP at: <url>
- Navigation map: .fullstack/testing/navigation-map.md

For each user flow found in Lanhu, generate minimum THREE test cases:

TC-<MODULE>-<N>-01 (Happy Path):
  fr_ref: <Lanhu flow name>
  type: happy_path
  priority: P0
  Given: <auth state + precondition>
  When: <action sequence using EXACT navigation map steps — route, button text, field labels>
  Then: <observable result — what URL, what element visible, what data>

TC-<MODULE>-<N>-02 (Sad Path):
  type: sad_path | permission
  Given: <invalid state or wrong role>
  When: <same action>
  Then: <error message / redirect / hidden element>

TC-<MODULE>-<N>-03 (Boundary — BVA):
  type: boundary
  target_field: <field from nav map + constraint>
  cases: min-1→reject / min→accept / max→accept / max+1→reject

Also add per-feature:
  TC-PERM-xxx: unauthenticated → 401/redirect; wrong role → 403/hidden
  TC-STATE-xxx: illegal state transition → error (if stateful entity exists)

Use CONCRETE navigation steps from the navigation map. No abstract steps.
Write to .fullstack/tests/test-cases.md with summary table at top.
EOF
```

### 2C — Generate from manual description (standalone source choice 3)

Collect scenarios via `AskUserQuestion`:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
请描述要测试的业务场景（可多个，换行分隔）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
示例:
  管理员创建一个互动培训，填写名称和时间，保存后在列表中验证
  普通用户尝试访问管理员专属页面，应被拒绝
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Convert user-described scenarios into structured BDD test cases.

User scenarios:
<scenarios from input>

Navigation map: .fullstack/testing/navigation-map.md
(Use it to resolve all navigation steps to concrete routes and element texts.)

For each scenario generate:
- 1 happy path (exact navigation steps from nav map)
- 1 sad path (error or permission failure)
- BVA cases for any mentioned input fields (min/max boundaries)

Write to .fullstack/tests/test-cases.md with summary table.
EOF
```

---

## Step 3 — Mark state, select scope, and route

If in FSE pipeline:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state TESTING_IN_PROGRESS
```

#### Test scope selection (ask once, standalone mode only)

Use `AskUserQuestion`:
```
测试范围:
  1. 完整测试 — 运行所有测试用例（P0 + P1 + P2）
  2. 冒烟测试 — 仅运行 P0 优先级用例（快速验证核心流程）
```

In pipeline mode: always run full scope.

If **冒烟测试** selected: filter test plan to P0 cases only before execution.

Route based on mode:
- `backend` → **Backend API Testing Path**
- `frontend / full / frontend-ext` → **Browser Flow Testing Path**
- `lite` → **Lite Smoke Test Path**
- Standalone "both" choice → run API path first, then Browser path

---

## Backend API Testing Path (mode: backend or standalone API choice)

### Generate API test plan

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" get-test-config
```

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Generate a complete API test plan.

PRIMARY INPUT (load if exists): .fullstack/tests/test-cases.md
  — Extract API-testable cases. Add HTTP execution detail to each.

SUPPLEMENTARY:
- Contract: .fullstack/contracts/openapi.yaml (if exists)
- Navigation map: .fullstack/testing/navigation-map.md (business context)
- Requirements: .fullstack/requirements/confirmed.md (if exists)

For each test case:

TC-BE-xxx:
  name: <descriptive>
  fr_ref: <source reference>
  type: happy_path | sad_path | boundary | permission | state_transition | concurrency
  endpoint: <METHOD /path>
  preconditions: <data state, auth role>
  request:
    headers: { Authorization: "Bearer <token_for_role>" }
    body: { ... }
  expected_response_contains: { ... }
  priority: P0 | P1 | P2

Mandatory methodology coverage:
  BVA: for parameters with length/range constraints → test min-1/min/max/max+1
  State Transition: for stateful resources → valid transition succeeds, illegal transition errors
  Permission Boundary:
    - No token → expect 401
    - Wrong-role token → expect 403
    - Valid token + wrong-owner ID → expect 403 (IDOR check)

Write to .fullstack/tests/api-test-plan.md
Include summary table at top: | TC ID | Type | Priority | Endpoint | Description |
EOF
```

### Execute API tests

```bash
codeagent-wrapper --agent develop - <backend_path> <<'EOF'
Execute all API test cases from .fullstack/tests/api-test-plan.md

Backend base URL: <test_config.base_url>
Auth accounts: <test_config.accounts as JSON>

For each test case:
1. Build and send HTTP request using curl
2. Assert: status code matches, response body contains expected fields
3. Record: PASS or FAIL with specific reason (status mismatch / missing field / wrong value)

Write results to .fullstack/tests/api-results-round-<N>.md
Print summary: <pass_count> passed / <fail_count> failed
EOF
```

Proceed to **Fix Cycle** for any failures.

---

## Browser Flow Testing Path (modes: frontend, full, frontend-ext, or standalone browser choice)

### Verify Playwright MCP

```bash
claude mcp list 2>/dev/null | grep -i playwright | head -3 || echo "MCP_MISSING"
```

If MCP_MISSING:
```
阻断：Playwright MCP 未找到。
请检查：claude mcp list — 确认 'playwright' 已列出并运行。
启用后重新执行 /fse-test。
```

### Generate browser test plan with navigation context

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" get-test-config
```

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Generate a Playwright browser test plan.

INPUTS:
- Test cases (primary): .fullstack/tests/test-cases.md
- Navigation map (REQUIRED): .fullstack/testing/navigation-map.md
- Base URL: <test_config.base_url>
- Test accounts: <test_config.accounts>

CRITICAL: Every step must use CONCRETE information from the navigation map.
  WRONG: "Navigate to the training page"
  RIGHT: "Navigate to <base_url>/interaction/training/list"
  WRONG: "Click the create button"
  RIGHT: "Click button with text '创建培训'"

For each test case:

TC-xxx:
  name: <descriptive>
  fr_ref: <reference>
  type: happy_path | sad_path | boundary | permission | state_transition | concurrency
  account: admin | user | none
  preconditions: <login state, required data>
  steps:
    1. Navigate to <base_url>/login
    2. Fill input[placeholder or label matching "用户名"] with "<account.username>"
    3. Fill input[type="password"] with "<account.password>"
    4. Click button "登录"
    5. Verify: URL contains "<dashboard_route_from_nav_map>"
    6. Click: "<exact Chinese menu text from nav map>"
    7. Click: "<exact Chinese submenu text from nav map>"
    8. Verify: URL is "<route_from_nav_map>"
    ... (continue with exact element texts from nav map)
  expected_result: <precise DOM state or URL that must be true>
  priority: P0 | P1 | P2

Include all methodology cases:
  BVA: use exact field labels and maxlength values from navigation map
  State Transition: use exact button/status texts from navigation map
  Permission: no-auth case (skip login steps), wrong-role case (use different account)

Write to .fullstack/tests/test-plan.md
Summary table: | TC ID | Type | Priority | Account | Route | Description |
EOF
```

### Execute test rounds (max 3 total across fix cycles)

Use Playwright MCP to execute each test case.

For each test case:
1. Follow steps exactly as written in the plan (concrete routes and element texts from nav map)
2. Assert the expected result
3. On failure: capture screenshot to `.fullstack/tests/screenshots/TC-<id>-round<N>-fail.png`
4. Record: PASS or FAIL with specific reason

Write results to `.fullstack/tests/results-round-<N>.md`.

---

## Fix Cycle (shared by API and Browser paths)

### Step A — Always: Generate Bug Reports

For EVERY failing test, regardless of environment or TAPD availability,
generate a bug report at `.fullstack/tests/bugs/BUG-<TC_ID>.md`:

```markdown
# BUG: <test case name>

TC ID: <id>  |  Priority: <P0|P1|P2>  |  Round: <N>
Environment: <env_name> (<base_url>)
Timestamp: <ISO timestamp>
Test Account: role=<role> username=<username>

## 复现步骤
<numbered steps from the test plan up to the point of failure>

## 预期结果
<expected_result from the test case>

## 实际结果
<what actually happened — error message shown, missing element, wrong data, unexpected redirect>

## 截图
<relative path: .fullstack/tests/screenshots/TC-<id>-round<N>-fail.png>
(or "未截图" if API test)

## 影响需求
<fr_ref from test case>

## 附加信息
Browser: Chromium (Playwright) | HTTP Client (curl)
Navigation Map: <Generated timestamp from map header>
```

Register each failure in workspace:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" add-issue \
  --phase testing --text "TC-<id>: <failure summary>" --severity blocking
```

After writing individual reports, generate a consolidated summary at
`.fullstack/tests/bugs/BUG-SUMMARY.md` listing all bugs with TC ID, priority, and one-line description.

---

### Step B — Determine fix strategy by environment type

```bash
ENV_TYPE=$(python "$HOME/.claude/skills/fse/scripts/workspace.py" get-test-env | grep "^type:" | awk '{print $2}')
```

---

### Strategy LOCAL (type=local) — Auto-fix loop

Delegate to develop agent:
```bash
codeagent-wrapper --agent develop - <project_path> <<'EOF'
Fix the test failures documented in .fullstack/tests/failures-round-<N>.md.

For each failure:
  - Diagnose root cause from the description and screenshot
  - Apply the minimal targeted fix
  - Do not touch unrelated code

Context files:
  - Navigation map: .fullstack/testing/navigation-map.md
  - Requirements: .fullstack/requirements/confirmed.md (if exists)
  - Contract: .fullstack/contracts/openapi.yaml (if exists)
  - Bug reports: .fullstack/tests/bugs/BUG-*.md
EOF
```

**Mandatory code review after every fix:**

```bash
codeagent-wrapper --parallel <<'EOF'
---TASK---
id: review_fix_correctness
agent: code-reviewer
workdir: <project_path>
---CONTENT---
Review fix for test failures. Scope: git diff HEAD~1

1. Fix targets actual root cause (not superficial patch to pass test)
2. No regression in adjacent functionality
3. SOLID: Single Responsibility, Open/Closed respected?
4. OWASP: No new injection / IDOR / auth bypass introduced?
5. Contract: if API changed, still matches openapi.yaml?

Confidence 0-100. Only report ≥ 80. Classify: Critical | Important.

---TASK---
id: review_fix_simplicity
agent: code-reviewer
workdir: <project_path>
---CONTENT---
Review fix for KISS. Scope: git diff HEAD~1
Is the change minimal and targeted? No over-engineering?
Confidence ≥ 80. Classify: Critical | Important.
EOF
```

- **Critical** → `AskUserQuestion`: "立即修复 / 按现状继续"
- **Important** → auto-fix via develop agent

#### Post-fix: Notify User to Restart Services Before Retest

After fse-dev fix completes, use `AskUserQuestion`:

```
fse-dev 已完成代码修复。

请重启以下服务以加载最新代码：
  • <name>（端口 <port>）  启动命令: <start_cmd>

重启完成后选择继续。
  1. 已重启，开始重新测试
  2. 停止测试
```

After user confirms restart, re-scan:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" check-services
```

All UP → re-run only the previously failed tests. Repeat up to round 3 total.

---

### Strategy REMOTE (type=remote) — Bug Report + Optional TAPD

Bug reports are already generated (Step A). Now handle submission.

**Check TAPD availability:**
```bash
claude mcp list 2>/dev/null | grep -i tapd | head -1 || echo "TAPD_UNAVAILABLE"
```

**If TAPD_UNAVAILABLE**:
- Continue without submission.
- Output at end of test run:
  ```
  Bug 报告已生成（<N> 条）：.fullstack/tests/bugs/
  TAPD MCP 未配置，请手动提交上述 Bug 报告。
  ```

**If TAPD available** AND environment has `tapd_project_id`:
- Use `AskUserQuestion`:
  ```
  发现 <N> 个测试失败，Bug 报告已生成。
  是否自动提交到 TAPD（项目 <tapd_project_id>）？
    1. 是 — 立即提交所有 Bug
    2. 否 — 仅保留本地报告文件
  ```

If yes, for each bug:
1. Search TAPD for open bugs with same title (dedup check)
2. If found: add comment with new failure details + attach screenshot
3. If not found: create new bug with:
   - Title: `[<env_name>] TC-<id>: <bug name>`
   - Description: full BUG-<TC_ID>.md content
   - Priority: P0→紧急 / P1→高 / P2→中
   - Screenshot attachment

**Do NOT attempt to fix code** — remote environment, changes require a deployment cycle.

Output after remote testing:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
远程环境测试完成 [<env_name>]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
通过: <N>  |  失败: <N>
Bug 报告: .fullstack/tests/bugs/BUG-SUMMARY.md
TAPD 提交: <N> 条新建 / <N> 条追加评论 (或: 未提交)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Round limit (local only)

After round 3 with remaining failures, escalate via `AskUserQuestion`:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测试 — 已达最大修复轮次 (3/3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
仍未解决的失败:
<TC ID + brief reason for each>

  1. 继续测试 — 再增加一轮修复
  2. 接受失败 — 记录为已知问题，继续流程
  3. 停止 — 我来手动处理
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Lite Smoke Test Path (mode: lite)

Use `AskUserQuestion`:
```
是否执行快速冒烟测试？
  1. 是 — 浏览器截图验证主页面可访问
  2. 否 — 跳过测试，直接标记完成
```

If yes: navigate to `<base_url>` with Playwright, take a screenshot, verify page title loads.
No fix cycle, no rounds.

---

## Completion

If in FSE pipeline:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state REPORTING
```

Write `.fullstack/tests/final-report.md`:

```markdown
# 测试报告

环境: <env_name> (<type>)  |  模式: <api | browser | both | smoke>
完成时间: <timestamp>  |  修复轮次: <N> (local only)

## 结果概览
| 指标 | 数量 |
|------|------|
| 测试用例总计 | N |
| 通过 | N |
| 失败（已修复，local）| N |
| 失败（Bug 已记录）| N |
| 跳过（账号不可用）| N |
| 覆盖 FR 数量 | N / M |

## Bug 报告
位置: .fullstack/tests/bugs/BUG-SUMMARY.md
TAPD 提交: <N> 条 (或: 未提交)

## 导航地图
生成时间: <from map header>  |  前端 Git Commit: <from map header>

## 已验证条目
- [x] TC-001: <description>
- [ ] TC-002: <description> — FAILED: <reason>

## 注意事项
测试数据清理：本次测试可能创建了临时数据，请人工检查并清理。
涉及的数据类型: <list any entities created during tests>
```

Output:
```
测试完成  [<env_name> · <mode>]
通过: <N> / <total>  |  Bug: <N> 条
Bug 报告: .fullstack/tests/bugs/BUG-SUMMARY.md
<promise>FSE_PHASE_COMPLETE</promise>
```
