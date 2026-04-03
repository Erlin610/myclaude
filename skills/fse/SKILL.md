---
name: fse
description: Full-stack engineer orchestrator. Routes to sub-skills based on workspace state and selected mode. Supports 5 modes: full, backend, frontend, frontend-ext, lite. Manages the complete feature development lifecycle with persistence, mandatory code review gates, and integration testing.
---

# FSE — Full-Stack Engineer Orchestrator

Stateful orchestrator for full-stack feature development across multiple frontend and backend projects. All code changes are delegated to codeagent-wrapper. Never write code directly.

## Language Requirement

**All user-facing output MUST be in Chinese (Simplified).** This includes all prompts, questions, status banners, error messages, confirmation gates, and progress displays shown to the user. Internal skill instructions may remain in English.

## Hard Constraints

1. **Never write code directly.** All implementation goes through `fse-dev` → `codeagent-wrapper`.
2. **No fallbacks.** codeagent-wrapper unavailable → BLOCK. Lanhu MCP unavailable → BLOCK.
3. **State persists in `.fullstack/workspace.json`** in the current working directory.
4. **Every confirmation gate requires explicit user approval** before state advances.
5. **Code review is mandatory after every development batch** — never skip regardless of mode.
6. **First-principles reasoning is applied at every phase** — especially requirements.
7. **All user-facing questions, choices, and confirmations MUST use the `AskUserQuestion` tool.** Never output a text prompt and wait for free-form input — always use AskUserQuestion with structured options. For text input fields (paths, URLs, etc.), use AskUserQuestion with a descriptive question and let the user type via the "Other" option.

## Activation

`/fse` or `/fse <subcommand>` from within the workspace directory (user must `cd` in first).

## Modes

| Mode | Scope | Phases |
|------|-------|--------|
| `full` | backend + frontend | requirements → analysis → contract → dev → manual → integration → test → **report** |
| `backend` | backend only | requirements → analysis → contract → dev → manual → API test → **report** |
| `frontend` | frontend only | requirements → analysis → dev → integration (own backend) → test → **report** |
| `frontend-ext` | frontend only | requirements → analysis → dev → integration (external backend) → test → **report** |
| `lite` | user-selected | quick requirements → quick analysis → dev → review → **report** |

## Startup Protocol

Steps 3 and 4 run only for new features. Steps 1, 2, 5, 6 run on every invocation.

### Step 1 — Detect workspace

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" status
```

**NOT_FOUND (exit 1)** → No workspace. Invoke `fse-init` immediately, then continue from Step 3.

**Found** → Start session and read current state:

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" session-start
python "$HOME/.claude/skills/fse/scripts/workspace.py" get-mode
```

---

### Step 2 — Session picker

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" session-list
```

**Skip condition**: output is `NO_SESSIONS` AND state is `WORKSPACE_READY` → go directly to Step 3.

Otherwise, use `AskUserQuestion` with these options:

- If current state is not `WORKSPACE_READY`, add at **top**:
  ```
  label:       ▶ 继续当前工作
  description: 当前阶段：<PHASE_LABEL>  |  模式：<current_mode>
  ```
- One option per saved session (sorted by `saved_at` descending):
  ```
  label:       <name>（<badge> · <mode>）
  description: 最后阶段：<state_label>  |  <saved_at 本地日期>
  ```
  Badges: `suspended` → `⏸ 已暂存`, `in_progress` → `▶ 进行中`, `completed` → `✅ 已完成`
- Always at **bottom**:
  ```
  label:       🆕 开始新需求
  description: 清空当前进度，重新选择模式和分支
  ```

**User selects a saved session**:
1. If current state is not `WORKSPACE_READY`, mark it suspended:
   ```bash
   python "$HOME/.claude/skills/fse/scripts/workspace.py" session-update-status \
     --session-id <current_feature_id> --status suspended
   ```
2. Restore selected session:
   ```bash
   python "$HOME/.claude/skills/fse/scripts/workspace.py" session-restore \
     --session-id <selected_session_id>
   python "$HOME/.claude/skills/fse/scripts/workspace.py" session-start
   ```
3. Git branch check: read restored project branch entries, use `AskUserQuestion` to confirm user has switched branches. Wait for confirmation before proceeding.
4. Scope extension check: if restored session has `mode=backend` and `state=COMPLETED`, ask whether to continue with frontend:
   - Yes → `set-mode full --scope frontend,backend` + `set-state CONTRACT_CONFIRMED`
   - No → continue unchanged
5. Skip to Step 5.

**User selects "▶ 继续当前工作"** → skip to Step 5.

**User selects "🆕 开始新需求"**:
1. If current state is not `WORKSPACE_READY` or `COMPLETED`, mark suspended:
   ```bash
   python "$HOME/.claude/skills/fse/scripts/workspace.py" session-update-status \
     --session-id <current_feature_id> --status suspended
   ```
2. Reset state:
   ```bash
   python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state WORKSPACE_READY
   ```
3. Continue to Step 3.

---

### Step 3 — Mode selection (new feature only)

Trigger: state is `WORKSPACE_READY`.

Use `AskUserQuestion` to present mode options:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FSE — 请选择本次功能的开发模式
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  full         — 后端 + 前端 + 联调 + 测试（完整新功能）
  backend      — 仅后端 + API 测试
  frontend     — 仅前端 + 联调（后端已在运行）
  frontend-ext — 仅前端 + 对接外部后端
  lite         — 快速修复（≤5 文件，跳过仪式性阶段）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Follow-up questions per mode (use `AskUserQuestion`):

- **`frontend-ext`**: collect external backend info (base URL, auth, API docs):
  ```bash
  python "$HOME/.claude/skills/fse/scripts/workspace.py" set-integration-target \
    --type external --base-url "<url>" --auth-type <type> --auth-value "<val>" \
    --api-docs-url "<swagger_url>"
  ```
- **`lite`**: ask which projects are in scope (frontend+backend / backend only / frontend only).

Register mode:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-mode <mode> [--scope frontend,backend]
```

---

### Step 4 — Branch confirmation (new feature only, mandatory)

Trigger: immediately after Step 3. Run once per in-scope project.

Read current branch per project:
```bash
git -C <project_path> rev-parse --abbrev-ref HEAD
```

Suggest branch name: `feat/<short-slug>-<YYYYMMDD>` (slug from user description or mode name).

Use `AskUserQuestion` for each project:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
分支确认：<project_name>（<type>）
当前分支：<current_branch>
建议分支：<suggested_branch>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Options: `使用建议分支 <suggested_branch>` / `使用当前分支 <current_branch>` / Other (custom name)

After confirmation:
```bash
git -C <project_path> checkout -b <branch_name> 2>/dev/null \
  || git -C <project_path> checkout <branch_name>

python "$HOME/.claude/skills/fse/scripts/workspace.py" set-branch \
  --name "<project_name>" \
  --base "<base_branch>" \
  --feature "<branch_name>" \
  --switched true
```

> **Rule:** Even if the user picks the current branch, always call `set-branch` to record it in workspace.json. Resume sessions depend on this to know which branch to check out.

---

### Step 5 — Status banner (always show)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FSE 工作区：<workspace_id>
模式：<MODE>  |  阶段：<PHASE_LABEL>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<per-project: name · branch · tech stack>

<phase checklist for current mode, marked complete/active/pending>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
继续执行：<current phase>...
```

---

### Step 6 — 按状态路由（每次必须执行）

#### Modes: full / backend / frontend / frontend-ext

| State | Action |
|-------|--------|
| WORKSPACE_READY | Invoke fse-requirements |
| REQUIREMENTS_DRAFTING | Resume fse-requirements |
| REQUIREMENTS_CONFIRMED | Invoke fse-analysis |
| ANALYSIS_IN_PROGRESS | Resume fse-analysis |
| ANALYSIS_CONFIRMED | `full/backend` → fse-contract · `frontend/frontend-ext` → fse-dev |
| CONTRACT_DEFINING | Resume fse-contract |
| CONTRACT_CONFIRMED | Invoke fse-dev |
| DEVELOPMENT_IN_PROGRESS | Resume fse-dev |
| DEVELOPMENT_DONE | `full` → fse-manual · `backend` → fse-manual · `frontend/frontend-ext` → fse-integration |
| MANUAL_TASKS_PENDING | Resume fse-manual |
| MANUAL_TASKS_DONE | `full` → fse-integration · `backend` → fse-test（跳过联调） |
| INTEGRATION_IN_PROGRESS | Resume fse-integration |
| INTEGRATION_PASSED | Invoke fse-test |
| TESTING_IN_PROGRESS | Resume fse-test |
| REPORTING           | Invoke fse-report → generates DELIVERY-REPORT.md → COMPLETED |
| COMPLETED           | Show completion summary |

> **backend 模式**：MANUAL_TASKS_DONE 直接跳到 fse-test（跳过 INTEGRATION 阶段）。
> **frontend / frontend-ext 模式**：跳过 CONTRACT 和 MANUAL_TASKS 阶段（DEVELOPMENT_DONE → fse-integration）。

#### Mode: lite

Lite uses a compressed flow:

| State | Action |
|-------|--------|
| WORKSPACE_READY | Quick requirements (inline, no Lanhu, no doc) |
| REQUIREMENTS_CONFIRMED | Quick analysis (file list only) |
| ANALYSIS_CONFIRMED | Invoke fse-dev (full dev + mandatory review) |
| DEVELOPMENT_DONE | Invoke fse-test (optional smoke test) |
| REPORTING | Invoke fse-report → COMPLETED |

Lite skips: Lanhu MCP fetch, requirements doc, contract, manual tasks, integration loop.
Lite never skips: code review.

## Subcommands

```
/fse              — auto-detect, session picker if history exists, continue
/fse init         — force re-initialize workspace
/fse status       — show progress.md only
/fse step <name>  — jump to phase (requires confirmation)
/fse suspend      — save current session and return to session picker
```

### /fse suspend

Delegates immediately to the `fse-suspend` skill. No further action in this orchestrator.

## 持续修改指南（功能交付后的后续改动）

| 场景 | 推荐命令 | 说明 |
|------|---------|------|
| 小改动、bug fix（≤5 文件） | `/fse` → 选 `lite` 模式 | 走完整 code review，维持 session 历史 |
| 需求有遗漏，需补某个阶段 | `/fse` → session picker 恢复 → `/fse step dev` | 跳回开发阶段重跑 |
| 与原需求完全独立的新改动 | `/do <描述>` | 轻量，不依赖工作区上下文 |
| 大范围重构或新功能 | `/fse` → `🆕 开始新需求` | 走完整 FSE 流程 |

> **`lite` 模式不跳过 code review**。即使是小修改，review 步骤（置信度评分 + CLAUDE.md 对齐）也必须执行。

## Completion

When state is COMPLETED (set by fse-report after generating DELIVERY-REPORT.md):

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" progress
```

If a session was saved for the current feature (i.e. a session in `.fullstack/sessions/` has
`current_state` matching the last non-COMPLETED state), update its status to `completed`:

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" session-save --status completed
```

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FSE 功能开发完成  [<mode>]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
详见 progress.md 和 DELIVERY-REPORT.md。
<promise>FSE_COMPLETE</promise>
```
