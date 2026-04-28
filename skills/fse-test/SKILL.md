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
9. **未验证 = 失败。这是不可逾越的红线。**
   只有两种合法的测试结果：`✅ 通过`（已执行 + 断言全部通过）和 `❌ 失败`（其他一切情况）。
   不存在第三种状态。具体说：
   - 前置条件未满足 → ❌ 失败（原因：前置条件未满足）
   - 组件/元素找不到 → ❌ 失败（原因：UI 元素无法定位）
   - 功能未实现 → ❌ 失败（原因：功能缺失）
   - 手动跳过 → ❌ 失败（原因：需人工操作，自动化覆盖缺失）
   `test.skip()` 和静默 `return` 同样禁止——跳过 = 未验证 = 失败。
   执行清单只有两列终态：`✅ 通过` 和 `❌ 失败（原因）`。

10. **测试必须自建前置条件，不得依赖人工操作。**
    如果一个测试用例需要"活跃课堂"、"学员已提交互动"、"存在某条数据"等前置条件，
    测试本身必须通过 API 调用创建该条件，然后在测试结束后清理（teardown）。
    不允许出现"需要先手动开课才能测"的情况——那是测试设计缺陷，不是环境问题。
    如果 API 无法创建某前置条件（无对应接口）→ 明确标记为 ❌ 失败（原因：前置条件无法自动创建，缺少 API）。
    通过 `AskUserQuestion` 告知用户并记录到 Bug 报告。

11. **组件找不到 → 先向用户确认，绝不自动标记通过。**
    在选择器解析阶段，若某个 UI 元素（弹幕、弹窗、动画等）在当前分支源码中找不到：
    - 不得生成假选择器
    - 不得静默跳过该用例
    - 必须用 `AskUserQuestion` 向用户确认：
      ```
      ⚠️ 无法在源码中找到以下 UI 组件，无法生成有效断言：
        - [组件名] — 搜索范围：src/**/*.vue
      可能原因：功能在其他分支 / 尚未实现 / 命名不同
      请选择：
        1. 功能在其他分支 — 告知分支名，切换后重新搜索
        2. 功能尚未实现 — 标记为 ❌ 失败（功能缺失）
        3. 提供正确文件路径 — 手动指定组件位置
      ```
    - 无论用户选哪项，该测试用例都不得标记为通过，直到断言可以真实执行。

12. **四种产生假通过的代码模式，永久禁止出现在生成的 spec 文件中：**
    - `if (await element.isVisible()) { /* 断言 */ }` — 前置失败时跳过所有断言 → 假通过
    - `return`（没有先调用 `test.fail()`）— Playwright 将早返回计为 PASS
    - `.catch(() => {})` 附加在任何 `expect()` 上 — 吞掉断言失败
    - `[class*="猜测"]` 属性选择器未经源码验证 — 可能匹配到错误元素

13. **选择器必须来自源码，不得猜测。** 在生成 spec 前，动态元素（动画、弹幕、Toast、弹窗）的 CSS class 必须从前端源码中读取。禁止 `[class*="xxx"]` 猜测模式。

14. **认证助手必须断言登录成功，禁止吞掉认证错误。这是红线规则。**
    生成的 `helpers/auth.ts` 每个角色的登录流程末尾 **必须** 有以下断言：
    ```typescript
    await expect(page).toHaveURL(/<登录后的路径正则>/, { timeout: 60000 })
    ```
    违禁模式（永久禁止）：
    - `await page.waitForURL(...).catch(() => {})` — 吞掉登录超时，测试继续在登录页执行
    - `await page.waitForLoadState(...).catch(() => {})` — 吞掉加载失败
    - 任何在认证流程中使用 `.catch(() => {})` 吞掉错误的写法
    
    导航到受保护路由后，**必须** 紧跟验证当前页面不是登录页：
    ```typescript
    await page.goto(`${BASE}/protected/route`)
    await expect(page).not.toHaveURL(/loginPage|login/, { timeout: 10000 })
    ```
    
    **根本原因**：登录失败时 `.catch(() => {})` 会让测试继续在登录页执行。后续 `page.goto('/protected')` 被重定向回登录页，截图显示登录页，但没有任何断言失败 → 假通过。这是"截图显示未登录却报告通过"问题的根源。

---

## Step 0 — Context Detection and Setup

### 0A — Detect execution context

```bash
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" status 2>/dev/null
```

**FOUND** → **Pipeline mode**: workspace and project paths are already configured.
  - Skip to Step 0C (credentials check).
  - Read mode from workspace: `python "$HOME/.claude/skills/fse-test/scripts/workspace.py" get-mode`

**NOT_FOUND** → **Standalone mode**: continue with Step 0B.

#### Derive TEST_DIR (both modes — do this immediately after context detection)

```bash
# Anchor to project root — TEST_DIR is relative to cwd
echo "Working directory: $(pwd)"
FEATURE_ID=$(python "$HOME/.claude/skills/fse-test/scripts/workspace.py" get-feature-id 2>/dev/null)
if [ -z "$FEATURE_ID" ] || [ "$FEATURE_ID" = "NOT_SET" ]; then
  FEATURE_ID="standalone-$(date +%Y%m%d-%H%M%S)"
fi
TEST_DIR=".fullstack/tests/$FEATURE_ID"
REQ_DIR=".fullstack/requirements/$FEATURE_ID"
CONTRACTS_DIR=".fullstack/contracts/$FEATURE_ID"
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
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" init "$(pwd)"
```

Register provided paths (detect tech stack inline via quick file check):
```bash
# For each provided project path:
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" add-project \
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
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" set-mode <backend|frontend|full>
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
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" list-test-envs
```

**Pipeline mode**: automatically use `local` environment — set it active, then verify `base_url` is populated. Never ask the user what port to use.

```bash
# Ensure local env exists with a base_url derived from the frontend project port
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" list-projects --type frontend
```

Parse the first frontend project's `port` field (e.g. `9527`). Then:

```bash
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" get-test-env --name local 2>/dev/null
```

- If `base_url` is already non-empty → use it as-is.
- If `base_url` is empty or env does not exist → auto-set from the frontend project port:

```bash
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" set-test-env \
  --name local --base-url "http://localhost:<frontend_port>" --type local
```

```bash
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" set-active-test-env --name local
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
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" set-test-env \
  --name "<name>" --base-url "<url>" --type <local|remote> [--tapd-project-id "<id>"]
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" set-active-test-env --name "<name>"
```

#### Configure accounts for active environment

```bash
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" get-test-env
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
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" add-test-account \
  --role "<role>" --username "<username>" --password "<password>"
```

---

### 0D — Service Check (both modes)

```bash
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" check-services
ENV_TYPE=$(python "$HOME/.claude/skills/fse-test/scripts/workspace.py" get-test-env | grep "^type:" | awk '{print $2}')
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
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" check-services
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

A Navigation Map answers three questions for every feature:
- **WHERE**: exact route URL + which menu path leads there
- **HOW MANY WAYS**: all navigation paths that reach this feature (direct, via breadcrumb, via action button)
- **SHORTEST PATH**: minimum steps from login → feature, used as the canonical test path

Without it, Playwright spec files must hardcode guesses about selectors and routes —
getting it wrong means brittle tests. A flat route table is not enough: a test agent that
knows `/student/courses` exists but doesn't know "click 我的课程 in the top nav" is still
navigating blindly. The map must capture the *reachability graph*, not just the route list.

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

- No output → map is **FRESH**. Output the following banner and read the map into context before proceeding:
  ```
  ✅ 导航地图已验证（最后生成：<MAP_DATE>，前端路由/导航无变更）
  路径：.fullstack/testing/navigation-map.md — 已加载到上下文
  ```
  Read `.fullstack/testing/navigation-map.md` fully into context now. Then skip to Step 2.

- Has output → map is **STALE** → print:
  ```
  ⚠️ 导航地图过期（自 <MAP_DATE> 后前端路由/导航有变更），正在更新导航地图…
  ```
  Then proceed to Step 1B.

### 1B — Generate Navigation Map

```bash
codeagent-wrapper --agent code-explorer - <frontend_path> <<'EOF'
Generate a complete Navigation Map for this frontend application.

PURPOSE: Used by a test agent to generate Playwright .spec.ts files.
Every value in this document must come directly from the source code —
exact routes, exact Chinese button/label text, exact form constraints.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — COMPLETE ROUTE ENUMERATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DO NOT assume router is in a single file. Run:
  find src/router -name "*.ts" -o -name "*.js" | sort
  find src -name "routes.ts" -o -name "routes.js" | sort
Read EVERY file found. For each route record:
  - Full resolved path (flatten nested routes: parent.path + child.path)
  - Component file (relative to src/)
  - Meta: roles/permissions required, page title, redirect target

Build a COMPLETE flat route table — no truncation, no "top N" shortcut.
If the router uses lazy imports like `() => import('./views/xxx.vue')`, still
record the component path from the import string.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — ROLE / PERSONA DETECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
From router meta, identify distinct user roles (e.g. student 学员, teacher 师资,
admin 管理员, judge 评委). For each role:
  - List the entry route after login (redirect or default home)
  - List which route prefixes belong to this role
  - Note the login route (may be shared or role-specific)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 — NAVIGATION STRUCTURE (MENU / SIDEBAR)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Search for sidebar/menu components:
  grep -r "Sidebar\|NavMenu\|AppMenu\|SideMenu\|el-menu\|a-menu" src/ --include="*.vue" -l
Read each found component fully. Extract the complete menu tree:
  - All menu items with EXACT display text (keep Chinese as-is)
  - The route each item navigates to
  - Which role(s) see this item (from v-if conditions)
Build per-role menu trees.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4 — PAGE ELEMENT EXTRACTION (ALL PAGES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For EVERY route found in Phase 1, read its component. Extract:
  a) INCOMING navigation: how does a user arrive here?
     - From which other pages via router-link / router.push / this.$router.push?
     - Via which button text (e.g. "进入课程", "查看详情")?
  b) OUTGOING navigation: where can the user go from here?
     - All router.push / this.$router.push / <router-link to="..."> targets
     - Map button text → destination route
  c) KEY ELEMENTS (for Playwright selectors):
     - Buttons: EXACT display text, action (submit / navigate / open-dialog)
     - Form fields: el-form-item label, v-model, required?, maxlength/rules
     - Table columns: header labels (for post-action verification)
     - Tabs: tab labels and which sub-route/view each activates

For large projects (>50 components): prioritize all list/index pages and
create/edit form pages first; then detail/view pages; then dialogs.
Do NOT stop at an arbitrary number — cover all routes from Phase 1.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 5 — REACHABILITY ANALYSIS (FEATURE TREE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Using the incoming/outgoing navigation data from Phase 4, build a directed
reachability graph. For each significant feature (a page where the user
performs a key action), find ALL paths from the login page:

  Path = login → [sequence of pages/clicks] → feature page
  Count steps (each page-transition = 1 step).
  Identify: shortest path, alternative paths.

Group features by role → module → feature name.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Write to .fullstack/testing/navigation-map.md:

```markdown
# Navigation Map

Generated: <ISO-8601 datetime>
Frontend: <absolute path>
Git commit: <git rev-parse HEAD>
Roles detected: <comma-separated list>
Total routes: <N>

---

## Feature Tree

### 角色：<role_name>（如 学员 / 师资 / 管理员）

Login entry: <login route> → after auth → <home route>

#### 模块：<module name>

##### 功能：<feature description>（如"进入课程上课"、"提交作品"）
Feature route: /xxx/yyy
Component: src/views/xxx/yyy.vue

路径（按步数排序）:
  ★ 最短路径（N步）: 首页 → 点击"<button text>" → [route /aaa] → 点击"<button text>" → [feature route]
  路径2（M步）:       顶部导航 → 点击"<menu item>" → [route /bbb] → ...
  路径3（M步）:       ...

前置条件: <e.g. 已报名该课程 / 已创建小组>

Key elements on this page:
| Element | Type | Exact Text / Label | Constraint | Action |
|---------|------|-------------------|------------|--------|
| 进入课程 | Button | "进入课程" | — | router.push('/course/:id/learn') |
| 课程名称 | Input | "课程名称" | required, maxlength=100 | v-model: form.name |

---

## Page Element Reference

### <route path> — <Chinese page name>
Component: src/views/xxx/yyy.vue
Roles: <who can access>
Reached from: <list of source pages + triggering action>
Leads to: <list of destination pages + triggering button>

Key elements:
| Element | Type | Exact Text / Label | Constraint | Action |
|---------|------|-------------------|------------|--------|

---

## Route Index
| Role | Module | Feature | Route | Component | Steps from login |
|------|--------|---------|-------|-----------|-----------------|
```

After writing, output a summary:
  导航地图已生成：<N> 个角色，<M> 个功能，<K> 条路由，最深路径 <X> 步
EOF
```

Output to user:
```
导航地图已生成 → .fullstack/testing/navigation-map.md
角色：<N>  |  功能：<M>  |  路由：<K>
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

> **MANDATORY: Read ALL pages before generating test cases.**
> Before calling the generation agent, use `lanhu_get_pages` to get the full page list.
> Then use `lanhu_get_ai_analyze_page_result` with `mode="text_only"` and `page_names="all"` to do a full global scan.
> After the global scan, do `mode="full"` reads grouped by module (per the FOUR-STAGE workflow).
> Only after ALL pages are read and understood may test case generation begin.
> **Never generate test cases after reading only a partial set of pages.**

#### Archive requirements source first

Before generating test cases, call `lanhu_get_pages` and write `$TEST_DIR/requirements-source.md`:

```markdown
# 需求来源存档

## 基本信息
来源类型: 蓝湖原型
Lanhu URL: <url>
文档名称: <document_name from lanhu_get_pages>
文档 ID: <document_id>
总页数: <total_pages>
读取时间: <ISO-8601 timestamp>
测试特性: <FEATURE_ID>

## 页面目录
<paste the full pages array from lanhu_get_pages as a table:>
| 序号 | 页面名称 | 路径 | 类型 |
|------|---------|------|------|

## 需求文本（全局扫描）
<paste the full text output from lanhu_get_ai_analyze_page_result mode="text_only" page_names="all">

## 模块详情
<for each module group analyzed with mode="full", paste the structured output here>
```

This file is the traceability record — every test case in `test-cases.md` must reference a page or flow found here.

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Generate BDD test cases from a Lanhu design.

Inputs:
- Lanhu URL: <url>
- REQUIRED: Read ALL pages via lanhu MCP — first call lanhu_get_pages, then lanhu_get_ai_analyze_page_result
  with mode="text_only" page_names="all" for global scan, then mode="full" per module group.
  Do NOT stop after reading a subset of pages. Read EVERY page in the document.
- Save ALL Lanhu content (page list + text scan + module details) to $TEST_DIR/requirements-source.md
  BEFORE writing test cases. This is the traceability record.
- Navigation map: .fullstack/testing/navigation-map.md (REQUIRED — cross-reference every test step
  against actual routes and element texts found in the map)

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
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" set-state TESTING_IN_PROGRESS
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

> **⛔ MANDATORY GATE — Browser mode only:**
> You MUST complete Steps 4A (Playwright workspace), 4B (config), and 4C (spec file generation)
> before ANY browser interaction.
> **NEVER use `mcp__playwright__` tools at this point.** MCP browser is reserved exclusively for
> Step 4E (failure investigation after `npx playwright test` has already run and produced failures).
> Jumping from test cases directly to MCP browser clicks is a violation of this skill — stop and
> generate spec files first.

### Step 3B — Precondition Analysis & API Setup

**Every test case that requires a specific data state must set it up via API. No human setup allowed.**

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Analyze $TEST_DIR/test-cases.md. Extract preconditions for every test case. Classify:

CATEGORY A — Can be set up via API (e.g. 开启课堂, 学员提交互动, 创建数据):
  Identify the API endpoint from contracts/openapi.yaml or api-surface.md.
  Write $TEST_DIR/precondition-setup.ts that:
    1. Calls the API to create/activate the required state
    2. Stores returned IDs/tokens in $TEST_DIR/fixtures.json
    3. Exports a teardown() to clean up after tests

CATEGORY B — Cannot be set up via API (no endpoint exists):
  Pre-mark those TC IDs as ❌ 失败 in the execution manifest.
  Reason: "前置条件无法自动构建：[描述]. 缺少 API 支持：[endpoint that would be needed]"
  These tests count as FAILED immediately — untestable = failed, not skipped.

CATEGORY C — No precondition (can run any time):
  No setup needed.

Write $TEST_DIR/precondition-map.md:
| TC ID | 前置条件 | 分类 | API 端点 | 备注 |
|-------|---------|------|---------|------|
| TC-SCORE-01 | 活跃课堂+学员互动记录 | A | POST /class/start | — |
| TC-EDIT-01  | 画布类互动进行中 | A | POST /interaction/start | — |
| TC-XXX-02   | 需物理设备 | B | — | ❌ 预标记失败 |
EOF
```

Run precondition setup:
```bash
cd "$TEST_DIR" && npx ts-node precondition-setup.ts 2>&1 | tee "$TEST_DIR/precondition-setup.log"
```

- Errors in log → those TC IDs → ❌ 失败（前置条件 API 调用失败），立即写入 manifest
- Success → `fixtures.json` populated → spec files read it for test data (IDs, tokens, etc.)

> **Red line**: CATEGORY B tests are pre-marked FAILED before any browser runs.
> They lower the pass rate. This is intentional — "can't automate" is a coverage gap, not a skip.

### Step 3C — Create Execution Manifest

Before generating spec files, create a manifest that tracks every TC ID:

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Read the summary table in $TEST_DIR/test-cases.md.
Extract every TC ID, its name, and priority.
Write $TEST_DIR/execution-manifest.md with every case set to ⏳ 待执行.

Output format exactly:

# 执行清单

特性: <FEATURE_ID>
创建时间: <ISO-8601 timestamp>
用例总数: <N>

| TC ID | 名称 | 优先级 | 状态 | 执行时间 | 备注 |
|-------|------|--------|------|----------|------|
| TC-XXX-001 | <name> | P0 | ⏳ 待执行 | — | — |
| TC-XXX-002 | <name> | P1 | ⏳ 待执行 | — | — |
...

Do NOT pre-fill any case as ✅ 通过 — every case starts as ⏳ 待执行.
EOF
```

Output:
```
执行清单已创建：<N> 条用例待执行
路径：$TEST_DIR/execution-manifest.md
```

> **Rule**: The manifest is the single source of truth for tested/untested status. A TC ID not updated to ✅/❌/⏭️ after the run is UNTESTED. No exceptions.

---

## Backend API Testing Path (mode: backend or standalone API choice)

### Generate API test plan

```bash
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" get-test-config
```

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Generate a complete API test plan.

PRIMARY INPUT (load if exists): $TEST_DIR/test-cases.md
  — Extract API-testable cases. Add HTTP execution detail to each.

SUPPLEMENTARY:
- Contract: $CONTRACTS_DIR/openapi.yaml (if exists)
- Navigation map: .fullstack/testing/navigation-map.md (business context)
- Requirements: $REQ_DIR/confirmed.md (if exists)

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

### Step 4C — Selector Resolution (MANDATORY pre-step before spec generation)

Before writing any spec file, scan the frontend source for every visual/dynamic element referenced in "Then" assertions:

```bash
codeagent-wrapper --agent code-explorer - <frontend_path> <<'EOF'
For each element listed below (from test-cases.md "Then" clauses), find its REAL CSS class and DOM structure.
Elements: <paste list — e.g. "弹幕", "评分下拉框", "锁定提示">

For each:
1. Search broadly: class name / Chinese text / component name / data attribute
2. Check ALL branches if on a feature branch — the component may be in main but not current branch
3. Extract: exact class names, data attrs, aria labels, timing (animation duration, auto-dismiss?)

Output table:
| 元素名 | 状态 | 选择器（真实） | 可见时长 | 备注 |
|--------|------|--------------|---------|------|
| 金色弹幕 | ✅ 已找到 | .gold-barrage-item | 3s | 动画后DOM移除 |
| 评分下拉框 | ✅ 已找到 | .score-dropdown | 持续可见 | |
| 某弹窗 | ❌ 未找到 | — | — | 当前分支无此组件 |
EOF
```

**For every element with status ❌ 未找到**: stop spec generation for those test cases. Use `AskUserQuestion`:

```
⚠️ 以下 UI 元素在当前分支源码中找不到，无法生成有效断言：
  - [元素名] — 已搜索：src/**/*.vue **.ts

可能原因：① 功能在其他分支未合并  ② 功能尚未实现  ③ 文件位置特殊

请选择：
  1. 功能在其他分支 — 告知分支名，切换后重新搜索
  2. 功能尚未实现 — 标记相关测试用例为 ❌ 失败（功能缺失）
  3. 提供组件文件路径 — 手动指定后继续
```

- 用户选 1 → 切换分支重新搜索，找到后继续
- 用户选 2 → 对应 TC IDs 在 manifest 标记为 ❌ 失败（原因：功能未实现），不生成 spec，继续其余用例
- 用户选 3 → 读指定文件提取选择器，继续

Write resolved selectors to `$TEST_DIR/selector-map.md`. Spec generation uses ONLY selectors from this map.

### Step 4C — Generate Playwright Spec Files

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Generate Playwright @playwright/test spec files from the test plan.

INPUTS:
- Test cases (primary): $TEST_DIR/test-cases.md
- Navigation map (REQUIRED): .fullstack/testing/navigation-map.md
- Selector map (REQUIRED): $TEST_DIR/selector-map.md — use ONLY these selectors for dynamic elements
- Base URL: <test_config.base_url>
- Test accounts: <test_config.accounts as JSON>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⛔ BANNED PATTERNS — DO NOT USE THESE IN ANY SPEC FILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. `if (await element.isVisible()) { /* assertions */ }`
   WHY BANNED: If element is not visible, the if-block is silently skipped.
   No assertion runs. Playwright reports PASS. This is a fake pass.
   FIX: Remove the if. Let `await expect(element).toBeVisible()` throw and fail the test.

2. `return` inside a test body without a preceding `test.fail()` / `expect.fail()`
   WHY BANNED: Playwright counts an early `return` as a PASS.
   FIX: If a precondition can't be met at runtime, call `expect.fail('前置条件未满足: ...')` — this
   records a real failure. `test.skip()` is ALSO banned — skipped = untested = failed.
   The only acceptable terminal states are PASS or FAIL.

3. `.catch(() => {})` on any `expect(...)` call
   WHY BANNED: Swallows assertion failures. `await expect(x).not.toBeVisible().catch(() => {})` 
   will pass even if x IS visible — the failure is eaten.
   FIX: Remove .catch(). Let the assertion throw.

4. `[class*="guess"], [title*="guess"]` CSS attribute guesses without source verification
   WHY BANNED: Guessed selectors match nothing (or match the wrong element), producing either
   a timeout failure or a vacuous pass on an unrelated element.
   FIX: Use ONLY selectors from selector-map.md (sourced from actual component code).

5. `await page.waitForTimeout(N)` as the ONLY wait before a screenshot assertion
   WHY BANNED: A fixed delay doesn't guarantee the effect has appeared.
   FIX: Use `waitForFunction` or `waitForSelector` — they wait for the actual DOM event.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL rules for spec generation:
  1. One .spec.ts file per MODULE (group test cases by their TC ID prefix, e.g. TC-USER-* → user.spec.ts)
  2. Each test case becomes one `test(...)` block. test.describe groups by TC type.
  3. Use EXACT element selectors — prefer in this priority order:
     a. Selectors from selector-map.md (real CSS classes from source code) — for dynamic/visual elements
     b. page.getByRole('button', { name: '创建培训' }) — for stable interactive elements
     c. page.getByLabel('名称') — for form fields
     d. page.getByText('编辑').first() — for text content
     NEVER: page.locator('[class*="guess"]') — no guessing
  4. Login helper: extract repeated login steps into a shared beforeEach or helper function.
     Do NOT repeat login code in every test.
  5. Timeout: each navigation step uses { timeout: 60000 } — handles slow backends.
  6. After form submit: await expect(page).toHaveURL(/<expected_route>/, { timeout: 60000 })
  7. Failure screenshots are automatic (playwright.config.ts screenshot: "only-on-failure").
     ADDITIONALLY: for transient visual effects (animations, barrages, toasts), add an EXPLICIT
     screenshot inside the test body immediately after the `toBeVisible` assertion passes —
     that moment is when the element IS visible, so the screenshot captures it.
  8. Each test must be independent — no shared state between tests.
     Use unique test data (e.g. append Date.now() to names) to avoid conflicts.
  9. Precondition failures at runtime → FAIL immediately, never skip:
     ```typescript
     // Preconditions are set up BEFORE the test runs (see Step 3B precondition-setup.ts).
     // If a runtime check still fails, it means setup failed — treat as test failure:
     const fixtures = JSON.parse(fs.readFileSync('$TEST_DIR/fixtures.json', 'utf8'))
     if (!fixtures.activeClassId) {
       // This should never happen if setup succeeded, but if it does:
       expect.fail('前置条件未满足：活跃课堂未创建 — 检查 precondition-setup.log')
       // test.skip() is NOT used here — skip = hidden failure
     }
     // Everything below asserts. No conditional wrapping of assertions.
     await page.goto(fixtures.classUrl)
     await expect(page.locator('.score-btn')).toBeVisible()  // ← must run, must pass
     ```
  10. For transient elements (barrages, toasts, notifications that auto-dismiss):
     ```typescript
     // Wait for element to appear in DOM (not just be visible — it may fly past quickly)
     await page.waitForFunction(
       (selector) => document.querySelector(selector) !== null,
       '.actual-barrage-class',  // from selector-map.md
       { timeout: 8000 }
     )
     // Take screenshot IMMEDIATELY — element is in DOM right now
     await page.screenshot({ path: '...', fullPage: false })
     // Then verify text while still in DOM
     const barrage = page.locator('.actual-barrage-class').first()
     await expect(barrage).toContainText('恭喜', { timeout: 3000 })
     ```

  11. Login assertion rule (non-negotiable — prevents "unauthenticated page passes"):
      The generated `helpers/auth.ts` MUST use this pattern for every role:
      ```typescript
      // ✅ CORRECT — fails immediately if login didn't work
      async function loginAsTeacher(page: Page): Promise<void> {
        await page.goto(`${BASE}/student/loginPage/index`)
        await page.getByText('师资用户').click()
        await page.locator('input[placeholder*="手机号"]').fill(TEACHER.username)
        await page.locator('input[type="password"]').fill(TEACHER.password)
        await page.getByRole('button', { name: /登\s*录/ }).click()
        // MANDATORY assertion — if login failed, test fails HERE, not silently on the protected page
        await expect(page).toHaveURL(/mycurricular|SelectDepartLoginTeacher/, { timeout: 25000 })
        // Handle org selection if needed, then assert final state
        if (page.url().includes('SelectDepartLoginTeacher')) {
          await page.locator('.el-select').first().click()
          await page.locator('.el-select-dropdown__item').first().click()
          await page.locator('button', { hasText: '确认' }).click()
          await expect(page).toHaveURL(/mycurricular/, { timeout: 20000 })
        }
      }
      ```
      ```typescript
      // ❌ BANNED — swallows login failure, test continues on login page
      await page.waitForURL(/mycurricular/, { timeout: 25_000 }).catch(() => {})
      ```
      Additionally, after any `page.goto('/protected/route')`, immediately assert:
      ```typescript
      await expect(page).not.toHaveURL(/loginPage|login/, { timeout: 10000 })
      ```

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

#### Update Execution Manifest

After parsing pw-results.json, immediately update the manifest:

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Read $TEST_DIR/pw-results.json and $TEST_DIR/execution-manifest.md.

For each test result in the JSON:
  - status = "expected" (passed) → update matching TC ID row: ✅ 通过, set 执行时间 to now
  - status = "unexpected" (failed) → update to: ❌ 失败, set 执行时间, set 备注 to first error (≤80 chars)
  - status = "skipped" → update to: ⏭️ 跳过, set 备注 to reason

Match by TC ID in test title. If a test title contains the TC ID (e.g. "TC-LOGIN-001"), update that row.

Any row still showing ⏳ 待执行 after matching = UNTESTED — do NOT change it, it remains ⏳.

Rewrite $TEST_DIR/execution-manifest.md with the updated statuses.
Print one summary line:
  ✅ 通过: <N>  ❌ 失败: <N>  ⏭️ 跳过: <N>  ⏳ 未执行: <N>
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
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" add-issue \
  --phase testing --text "TC-<id>: <failure summary>" --severity blocking
```

After writing individual reports, generate a consolidated summary at
`$TEST_DIR/bugs/BUG-SUMMARY.md` listing all bugs with TC ID, priority, and one-line description.

---

## Fix Cycle (shared by API and Browser paths)

### Determine fix strategy by environment type

```bash
ENV_TYPE=$(python "$HOME/.claude/skills/fse-test/scripts/workspace.py" get-test-env | grep "^type:" | awk '{print $2}')
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
  - Requirements: $REQ_DIR/confirmed.md (if exists)
  - Contract: $CONTRACTS_DIR/openapi.yaml (if exists)
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
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" check-services
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

### Completion Gate — Mandatory before writing final report

The manifest has ONLY two valid terminal states: `✅ 通过` and `❌ 失败`.
Any row still showing `⏳ 待执行` at this point means a test that was supposed to run never ran → treat as `❌ 失败（原因：未执行到）`.

First, convert any remaining `⏳ 待执行` rows:
```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Read $TEST_DIR/execution-manifest.md.
For any row still showing ⏳ 待执行: change it to ❌ 失败, reason: "未执行到（测试中止或流程错误）".
Rewrite the manifest.
EOF
```

Then count:
```bash
TOTAL=$(grep -c "^| TC-" "$TEST_DIR/execution-manifest.md" 2>/dev/null || echo "0")
PASSED=$(grep -c "✅ 通过" "$TEST_DIR/execution-manifest.md" 2>/dev/null || echo "0")
FAILED=$(grep -c "❌ 失败" "$TEST_DIR/execution-manifest.md" 2>/dev/null || echo "0")
# TOTAL = PASSED + FAILED (no other states)
```

Determine completion status:
- `FAILED = 0` → `COMPLETION_STATUS="✅ 全部通过（${PASSED}/${TOTAL}）"`
- `FAILED > 0` AND all failures are "功能缺失/前置条件" → `COMPLETION_STATUS="⚠️ 测试完成，存在 ${FAILED} 项失败"`
- `FAILED > 0` AND any failure is actual assertion error → `COMPLETION_STATUS="❌ 测试完成，存在 ${FAILED} 项失败（含 Bug）"`

> **Red line**: There is no "未完成" status — once the gate runs, every case is either PASS or FAIL.
> The gate converts all undecided cases to FAIL automatically.

If in FSE pipeline:
```bash
python "$HOME/.claude/skills/fse-test/scripts/workspace.py" set-state REPORTING
```

Write `$TEST_DIR/final-report.md`:

```markdown
# 测试报告

环境: <env_name> (<type>)  |  模式: <api | browser | both | smoke>
完成时间: <timestamp>  |  修复轮次: <N> (local only)
完成状态: <COMPLETION_STATUS>

## 结果概览
| 指标 | 数量 |
|------|------|
| 测试用例总计 | N |
| ✅ 通过 | N |
| ❌ 失败（断言失败/Bug）| N |
| ❌ 失败（前置条件无法构建）| N |
| ❌ 失败（功能未实现）| N |
| ❌ 失败（其他原因）| N |
| **通过率** | PASSED / TOTAL |

> 通过率分母 = 全部用例（PASS + FAIL）。未验证 = 失败，不存在例外。

## 失败用例明细
<For each ❌ row: TC ID | 原因分类 | 具体原因 | 是否有 Bug 报告>

## 需求溯源
来源类型: <蓝湖原型 | 用户文件 | 手动描述>
原始需求: $TEST_DIR/requirements-source.md (or: 不适用)
Lanhu URL: <url if applicable, else —>
页面数: <N> (if Lanhu)

## Bug 报告
位置: $TEST_DIR/bugs/BUG-SUMMARY.md
TAPD 提交: <N> 条 (或: 未提交)

## Playwright 报告
HTML 报告: $TEST_DIR/pw-report/index.html
JSON 结果: $TEST_DIR/pw-results.json
执行清单: $TEST_DIR/execution-manifest.md

## 导航地图
生成时间: <from map header>  |  前端 Git Commit: <from map header>

## 用例执行状态
<Copy the full manifest table here — all TC IDs with their final status>

## 注意事项
测试数据清理：本次测试可能创建了临时数据，请人工检查并清理。
涉及的数据类型: <list any entities created during tests>
```

Output:
```
<COMPLETION_STATUS>  [<env_name> · <mode>]
已执行: <EXECUTED> / <TOTAL>  |  通过: <PASSED>  |  失败: <FAILED>  |  未执行: <UNTESTED>
Bug 报告: $TEST_DIR/bugs/BUG-SUMMARY.md
Playwright 报告: $TEST_DIR/pw-report/index.html
<promise>FSE_PHASE_COMPLETE</promise>
```
