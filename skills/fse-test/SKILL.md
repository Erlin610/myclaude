---
name: fse-test
description: Functional testing skill. Works both integrated in the FSE pipeline and as a fully standalone tool for QA team members. Builds a Navigation Map from the frontend project so Playwright tests navigate by known paths (never exploring blindly). Three test case sources — pre-generated from requirements, derived from Lanhu design, or manual user input. API testing (curl) for backend mode, browser flow testing (pre-generated @playwright/test scripts executed in parallel) for frontend/full mode. MCP browser retained only for failure investigation. Defects trigger fix + code review cycle (max 3 rounds).
---

# FSE-Test — Functional Testing

Two execution contexts:
- **Pipeline mode**: called by FSE orchestrator after development. Workspace exists, `test-cases.md` may be pre-generated, navigation map may exist. Skip straight to testing.
- **Standalone mode**: invoked directly with `/fse-test` by any team member. No prior FSE run required. Collects project paths, credentials, mode, and test case source from scratch.

## Language Requirement

**All user-facing output MUST be in Chinese (Simplified).** Internal skill instructions may remain in English.

## Hard Constraints

1. **Tests derive from real sources** — every test traces to a confirmed requirement, a Lanhu flow, or an explicit user-described scenario. Never fabricate scenarios.
2. **Navigation Map required for browser mode** — never generate Playwright spec files without a map. A test agent without a map is a new employee on their first day, clicking around randomly.
3. **@playwright/test is the primary browser test runner** — pre-generated `.spec.ts` files run via `npx playwright test`. Playwright MCP is ONLY for failure investigation and screenshot capture. Never execute browser tests step-by-step via MCP as the primary path.
4. **Fix cycle always includes code review** — same quality gate as `fse-dev`.
5. **Max fix rounds: 3.** After that, escalate to user.
6. **All user-facing questions MUST use `AskUserQuestion` tool.**
7. **NEVER tell the user to manually start services in remote env.** For local env, SHOW the start commands and ask the user to start manually — do NOT auto-start. Printing the start command IS the help. If services are still DOWN after user confirms restart, repeat the check once more.
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

#### Derive TEST_DIR (both modes — do this immediately after context detection)

```bash
# Anchor to project root — TEST_DIR is relative to cwd
echo "Working directory: $(pwd)"
FEATURE_ID=$(python "$HOME/.claude/skills/fse/scripts/workspace.py" get-feature-id 2>/dev/null)
if [ -z "$FEATURE_ID" ] || [ "$FEATURE_ID" = "NOT_SET" ]; then
  FEATURE_ID="standalone-$(date +%Y%m%d-%H%M%S)"
fi
TEST_DIR=".fullstack/tests/$FEATURE_ID"
mkdir -p "$TEST_DIR/bugs" "$TEST_DIR/specs" "$TEST_DIR/test-results"
echo "TEST_DIR: $TEST_DIR"
echo "FEATURE_ID: $FEATURE_ID"
```

> **All test output for this session goes under `$TEST_DIR/`.** Different features/requirements never overwrite each other. The navigation map (`.fullstack/testing/navigation-map.md`) is shared across sessions since it reflects the frontend codebase, not a specific feature.
>
> **Variable substitution rule**: `$FEATURE_ID` and `$TEST_DIR` are shell variables set above. Before ANY `codeagent-wrapper` call in subsequent steps, mentally substitute their actual values into the prompt text. Never pass the literal string `$FEATURE_ID` or `$TEST_DIR` to codeagent — always use the resolved value (e.g. `feat-login-20250115` or `.fullstack/tests/feat-login-20250115`).

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
  2. 页面流程测试 (Browser) — Playwright 脚本并行执行
  3. 两者都测
```

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-mode <backend|frontend|full>
```

#### Choose test case source

Use `AskUserQuestion`:
```
测试用例来源:
  1. 我的文件 — 提供测试用例文件路径（支持任意格式：md、txt、Excel 描述、Word 内容）
  2. 蓝湖设计稿 — 提供蓝湖 URL，AI 自动分析需求/设计稿生成用例
  3. 手动描述 — 直接描述要测试的业务场景，AI 结构化为用例
```

If source 1 selected, ask:
```
请提供测试用例文件的绝对路径（如 D:/projects/test-cases.md）：
```

Read the file at the provided path. AI will parse it regardless of format — structured BDD, simple list, numbered steps, or free-form description. Then copy/convert content into `$TEST_DIR/test-cases.md` as the working copy.

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

### 0D — Service Check (both modes)

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" check-services
ENV_TYPE=$(python "$HOME/.claude/skills/fse/scripts/workspace.py" get-test-env | grep "^type:" | awk '{print $2}')
```

**If all services are UP** → proceed to Step 1.

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

- All UP → proceed to Step 1.
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

Without it, Playwright spec files must hardcode guesses about selectors and routes —
getting it wrong means brittle tests. With it, spec generation has all exact element texts,
routes, and flow sequences before writing a single line of code.

### 1A — Check existence and freshness

```bash
test -f .fullstack/testing/navigation-map.md && echo "EXISTS" || echo "MISSING"
```

**If MISSING**: generate immediately (Step 1B). No prompt needed.

**If EXISTS**: check staleness against frontend git history:
```bash
MAP_DATE=$(grep "^Generated:" .fullstack/testing/navigation-map.md | head -1 | sed 's/Generated: //' | tr 'T' ' ')
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

PURPOSE: This document is used as context by a codeagent that generates Playwright
.spec.ts test files. Every piece of information must be verifiable in the source code —
exact route paths, exact button texts (Chinese), exact form field labels.

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

### 2A — User-provided file OR pipeline pre-generated file

**Standalone mode (source choice 1)**: user already provided a file path in Step 0B.

```bash
# Read the user-provided file (any format)
cat "<user_provided_path>"
```

Parse the content — accept any of these formats without requiring conversion upfront:
- BDD (Given/When/Then)
- Numbered list (`1. 登录系统 → 验证跳转到首页`)
- Table (`| TC-001 | 创建用户 | 填写姓名… | 列表可见 |`)
- Free-form paragraphs describing test scenarios

Copy to working path:
```bash
cp "<user_provided_path>" "$TEST_DIR/test-cases.md"
```

If the format is non-standard, normalize inline:
```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Normalize the test cases in $TEST_DIR/test-cases.md into structured BDD format.

Rules:
- Preserve ALL original test intent — do not add or remove scenarios
- Map each scenario to: TC ID, name, type (happy_path/sad_path/boundary/permission), priority (P0/P1/P2), Given/When/Then
- Use CONCRETE navigation steps from .fullstack/testing/navigation-map.md if it exists
- If nav map does not exist yet, keep steps abstract — they will be concretized in Step 4C spec generation
- Output: overwrite $TEST_DIR/test-cases.md with normalized content + summary table at top
EOF
```

```
已加载测试用例：<N> 条用例（来源：<user_provided_path>）
```
Skip to Step 3.

---

**Pipeline mode**: check for pre-generated file:

```bash
test -f "$TEST_DIR/test-cases.md" && echo "FOUND" || echo "MISSING"
```

If FOUND → skip to Step 3.

If MISSING → warn and generate from requirements:
```
未找到预生成测试用例，将从 confirmed.md 实时生成。
```

Then run the BDD generation prompt from fse-requirements Step 5.5 inline, writing to `$TEST_DIR/test-cases.md`.

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
Write to $TEST_DIR/test-cases.md with summary table at top.
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

Write to $TEST_DIR/test-cases.md with summary table.
EOF
```

---

## Step 3 — Mark State, Select Scope, and Route

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

If **冒烟测试** selected: filter test plan to P0 cases only before spec generation.

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

PRIMARY INPUT (load if exists): $TEST_DIR/test-cases.md
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

Write to $TEST_DIR/api-test-plan.md
Include summary table at top: | TC ID | Type | Priority | Endpoint | Description |
EOF
```

### Execute API tests

```bash
codeagent-wrapper --agent develop - <backend_path> <<'EOF'
Execute all API test cases from $TEST_DIR/api-test-plan.md

Backend base URL: <test_config.base_url>
Auth accounts: <test_config.accounts as JSON>

For each test case:
1. Build and send HTTP request using curl
2. Assert: status code matches, response body contains expected fields
3. Record: PASS or FAIL with specific reason (status mismatch / missing field / wrong value)

Write results to $TEST_DIR/api-results-round-<N>.md
Print summary: <pass_count> passed / <fail_count> failed
EOF
```

Proceed to **Fix Cycle** for any failures.

---

## Browser Flow Testing Path (modes: frontend, full, frontend-ext, or standalone browser choice)

### Step 4A — Initialize Playwright Workspace

Check for existing Playwright installation in `.fullstack/playwright/`:

```bash
test -f .fullstack/playwright/package.json && echo "EXISTS" || echo "MISSING"
```

**If MISSING** — create the isolated Playwright workspace:

```bash
mkdir -p .fullstack/playwright/tests
```

Write `.fullstack/playwright/package.json`:
```json
{
  "name": "fse-playwright-tests",
  "version": "1.0.0",
  "private": true,
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  }
}
```

Install dependencies and download browser:
```bash
cd .fullstack/playwright && npm install && npx playwright install chromium
```

> **Browser binary reuse**: If `@playwright/mcp` is installed globally, check whether its Chromium binary can be reused. Run `npx playwright install chromium` anyway — it is a no-op if the binary already exists.

**If EXISTS** — skip install, proceed directly to config generation.

### Step 4B — Generate Playwright Config

Generate `.fullstack/playwright/playwright.config.ts`:

> **Substitute actual values**: Replace `<FEATURE_ID>` with the real value of `$FEATURE_ID` and `<BASE_URL>` with the real base URL before calling codeagent.

```bash
codeagent-wrapper --agent code-architect - .fullstack/playwright <<'EOF'
Generate a playwright.config.ts file with the following settings.
All paths are relative to .fullstack/playwright/ where npx runs.

import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '../../tests/<FEATURE_ID>/specs',
  testMatch: '**/*.spec.ts',
  timeout: 60000,
  expect: { timeout: 10000 },
  retries: 0,
  workers: process.env.CI ? 2 : 4,
  reporter: [
    ['json', { outputFile: '../../tests/<FEATURE_ID>/pw-results.json' }],
    ['html', { outputFolder: '../../tests/<FEATURE_ID>/pw-report', open: 'never' }],
    ['line'],
  ],
  use: {
    baseURL: '<BASE_URL>',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'off',
  },
  outputDir: '../../tests/<FEATURE_ID>/test-results',
});

Write this exactly to playwright.config.ts with the <FEATURE_ID> and <BASE_URL> placeholders already substituted.
EOF
```

### Step 4C — Generate Playwright Spec Files

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Generate Playwright @playwright/test spec files from the test plan.

INPUTS:
- Test cases (primary): $TEST_DIR/test-cases.md
- Navigation map (REQUIRED): .fullstack/testing/navigation-map.md
- Base URL: <test_config.base_url>
- Test accounts: <test_config.accounts as JSON>

CRITICAL rules for spec generation:
  1. One .spec.ts file per MODULE (group test cases by their TC ID prefix, e.g. TC-USER-* → user.spec.ts)
  2. Each test case becomes one `test(...)` block. test.describe groups by TC type.
  3. Use EXACT element selectors derived from the navigation map:
     - Prefer: page.getByRole('button', { name: '创建培训' })
     - Prefer: page.getByLabel('名称')
     - Prefer: page.getByText('编辑').first()
     - Avoid: page.locator('.btn-primary') — fragile class selectors
  4. Login helper: extract repeated login steps into a shared beforeEach or helper function.
     Do NOT repeat login code in every test.
  5. Timeout: each navigation step uses { timeout: 60000 } — handles slow backends.
  6. After form submit: await expect(page).toHaveURL(/<expected_route>/, { timeout: 60000 })
  7. Failure screenshots are automatic (playwright.config.ts screenshot: "only-on-failure").
     Do not add manual screenshot calls in spec files.
  8. Each test must be independent — no shared state between tests.
     Use unique test data (e.g. append Date.now() to names) to avoid conflicts.

MULTI-USER / DUAL-BROWSER pattern (use when test case involves two roles interacting simultaneously):
  Trigger: test case describes Role A does X → Role B sees Y (e.g. messaging, notifications, shared state).
  Pattern: use `{ browser }` fixture instead of `{ page }`. Create two browserContexts (= two incognito windows).
  Each context has its own session/cookies — login independently.
  Steps interleave between the two pages to simulate real-time interaction.
  Real-time wait: use `await expect(pageB.getByText(...)).toBeVisible({ timeout: 15000 })` — allow up to 15s for WebSocket/SSE delivery.
  Always close both contexts in the test body (not afterEach) to avoid cross-test leakage.
  IMPORTANT — dual-browser tests MUST use serial mode to avoid parallel workers spawning 8+ browser contexts simultaneously:
    Add `test.describe.configure({ mode: 'serial' })` at the top of any dual-browser describe block.
  IMPORTANT — use unique room/channel IDs per test run to avoid workers interfering with each other's shared state:
    Generate IDs with `Date.now()` or a UUID, then create the room/channel via API or UI before both roles join.

EXAMPLE — dual-browser spec:
```typescript
import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

async function loginAs(page: Page, username: string, password: string): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('用户名').fill(username);
  await page.getByLabel('密码').fill(password);
  await page.getByRole('button', { name: '登录' }).click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 60000 });
}

test.describe('TC-MSG-1: 师生实时消息互通', () => {
  test.describe.configure({ mode: 'serial' }); // 防止并行worker冲突

  test('教师发送消息后学员端实时收到', async ({ browser }) => {
    // 两个独立上下文 = 两个无痕浏览器窗口
    const teacherCtx = await browser.newContext();
    const studentCtx = await browser.newContext();
    const teacherPage = await teacherCtx.newPage();
    const studentPage = await studentCtx.newPage();

    // 分别登录两个角色
    await loginAs(teacherPage, 'teacher01', 'pass123');
    await loginAs(studentPage, 'student01', 'pass456');

    // 使用唯一房间ID避免并行测试互相干扰
    const roomId = `room-${Date.now()}`;
    await teacherPage.goto(`/discussion/room/${roomId}`);
    await studentPage.goto(`/discussion/room/${roomId}`);

    // 教师端发消息
    const msg = `测试消息_${Date.now()}`;
    await teacherPage.getByPlaceholder('输入消息').fill(msg);
    await teacherPage.getByRole('button', { name: '发送' }).click();

    // 验证学员端实时收到（15s 内）
    await expect(studentPage.getByText(msg)).toBeVisible({ timeout: 15000 });

    await teacherCtx.close();
    await studentCtx.close();
  });
});
```

OUTPUT:
  Write each module's spec file to: $TEST_DIR/specs/<module>.spec.ts
  Print a summary: <N> spec files generated, <M> total test cases
  Note which tests use dual-browser pattern.
EOF
```

### Step 4D — Execute Tests

```bash
# Reporters are defined in playwright.config.ts — do NOT pass --reporter on CLI (overrides config)
cd .fullstack/playwright && npx playwright test 2>&1 | tee "../../tests/$FEATURE_ID/pw-run.log"
```

> Reporters defined in `playwright.config.ts` write JSON + HTML to `$TEST_DIR/`. The `line` reporter streams progress to terminal. Workers=`process.env.CI ? 2 : 4` runs tests in parallel — typical 20-test suite completes in ~2 minutes.

Parse results (use `<<EOF` without quotes so shell expands `$FEATURE_ID`):
```bash
python3 - <<EOF
import json, sys

with open(".fullstack/tests/$FEATURE_ID/pw-results.json") as f:
    data = json.load(f)

passed = 0
failed_ids = []
for s in data.get("suites", []):
    for t in s.get("specs", []):
        tests = t.get("tests", [])
        if not tests:
            continue
        results = tests[0].get("results", [])
        if all(r["status"] == "expected" for r in results):
            passed += 1
        else:
            failed_ids.append(t["title"])

failed = data["stats"]["unexpected"]
print(f"通过: {passed}  失败: {failed}")
for tc in failed_ids:
    print(f"  FAIL: {tc}")
EOF
```

**If all pass** → skip to Fix Cycle / Completion.

**If any fail** → proceed to **Failure Investigation** (Step 4E), then **Fix Cycle**.

### Step 4E — Failure Investigation (MCP Browser)

> This is the ONLY step where Playwright MCP browser is used. Do not use MCP for passing tests.

For each failed test case, use Playwright MCP to reproduce and capture evidence:

1. Open the failure screenshot from `$TEST_DIR/test-results/` (auto-captured by Playwright on failure)
2. If screenshot is insufficient: use `mcp__playwright__browser_navigate` to replay the failing steps
3. Capture additional screenshots or inspect DOM state via `mcp__playwright__browser_snapshot`
4. Record the actual error: what element was missing, what URL was wrong, what text was unexpected

Write a bug report for each failure at `$TEST_DIR/bugs/BUG-<TC_ID>.md`:

```markdown
# BUG: <test case name>

TC ID: <id>  |  Priority: <P0|P1|P2>  |  Round: <N>
Environment: <env_name> (<base_url>)
Timestamp: <ISO timestamp>
Test Account: role=<role> username=<username>

## 复现步骤
<numbered steps from the spec file up to the point of failure>

## 预期结果
<expected assertion from the spec>

## 实际结果
<actual error — timeout, element not found, wrong URL, unexpected text>

## 截图
<relative path: $TEST_DIR/test-results/<spec-name>/<filename>.png>

## 影响需求
<fr_ref from test case>

## 附加信息
Runner: @playwright/test (npx)  |  Browser: Chromium
Navigation Map: <Generated timestamp from map header>
```

Register each failure in workspace:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" add-issue \
  --phase testing --text "TC-<id>: <failure summary>" --severity blocking
```

After writing individual reports, generate a consolidated summary at
`$TEST_DIR/bugs/BUG-SUMMARY.md` listing all bugs with TC ID, priority, and one-line description.

---

## Fix Cycle (shared by API and Browser paths)

### Determine fix strategy by environment type

```bash
ENV_TYPE=$(python "$HOME/.claude/skills/fse/scripts/workspace.py" get-test-env | grep "^type:" | awk '{print $2}')
```

---

### Strategy LOCAL (type=local) — Auto-fix loop

Delegate to develop agent:
```bash
codeagent-wrapper --agent develop - <project_path> <<'EOF'
Fix the test failures documented in $TEST_DIR/bugs/BUG-*.md (round <N>).

For each failure:
  - Diagnose root cause from the description and screenshot
  - Apply the minimal targeted fix
  - Do not touch unrelated code

Context files:
  - Navigation map: .fullstack/testing/navigation-map.md
  - Requirements: .fullstack/requirements/confirmed.md (if exists)
  - Contract: .fullstack/contracts/openapi.yaml (if exists)
  - Bug reports: $TEST_DIR/bugs/BUG-*.md
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

After both parallel review tasks complete, collect their combined output:
- If either task reports **Critical** → `AskUserQuestion`: "立即修复 / 按现状继续"
- If either task reports **Important** only → auto-fix via develop agent
- If both tasks report nothing (confidence < 80) → proceed to retest

#### Post-fix: Notify User to Restart, Then Retest

After fix completes, use `AskUserQuestion`:

```
fse-dev 已完成代码修复。

请重启以下服务以加载最新代码：
  • <name>（端口 <port>）  启动命令: <start_cmd>

重启完成后选择继续。
  1. 已重启，开始重新测试
  2. 停止测试
```

After user confirms restart, re-scan services:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" check-services
```

All UP → re-run only failed tests (substitute actual round number for `<N>`):

**Browser path re-run:**
```bash
# Check if last-run tracking file exists
test -f .fullstack/playwright/.last-run.json && LAST_RUN="--last-failed" || LAST_RUN=""
cd .fullstack/playwright && npx playwright test $LAST_RUN 2>&1 | tee "../../tests/$FEATURE_ID/pw-run-round<N>.log"
```

> If `.last-run.json` is missing (e.g. working directory changed), Playwright runs all tests. In that case, pass the specific spec files containing failures instead:
> `npx playwright test "../../tests/$FEATURE_ID/specs/<failing-module>.spec.ts"`

**API path re-run:** re-execute only the failing TC IDs from the previous round.

Repeat up to round 3 total.

---

### Strategy REMOTE (type=remote) — Bug Report + Optional TAPD

Bug reports are already generated (Step 4E). Now handle submission.

**Check TAPD availability:**
```bash
claude mcp list 2>/dev/null | grep -i tapd | head -1 || echo "TAPD_UNAVAILABLE"
```

**If TAPD_UNAVAILABLE**:
- Continue without submission.
- Output at end of test run:
  ```
  Bug 报告已生成（<N> 条）：$TEST_DIR/bugs/
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
Bug 报告: $TEST_DIR/bugs/BUG-SUMMARY.md
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
  1. 是 — Playwright 脚本验证主页面可访问并截图
  2. 否 — 跳过测试，直接标记完成
```

If yes: generate a minimal `smoke.spec.ts` that navigates to `<base_url>`, verifies title loads, and captures a screenshot. Run via `npx playwright test smoke.spec.ts`.
No fix cycle, no rounds.

---

## Completion

If in FSE pipeline:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state REPORTING
```

Write `$TEST_DIR/final-report.md`:

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
位置: $TEST_DIR/bugs/BUG-SUMMARY.md
TAPD 提交: <N> 条 (或: 未提交)

## Playwright 报告
HTML 报告: $TEST_DIR/pw-report/index.html
JSON 结果: $TEST_DIR/pw-results.json

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
Bug 报告: $TEST_DIR/bugs/BUG-SUMMARY.md
Playwright 报告: $TEST_DIR/pw-report/index.html
<promise>FSE_PHASE_COMPLETE</promise>
```
