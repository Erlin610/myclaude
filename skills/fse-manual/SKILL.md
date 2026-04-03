---
name: fse-manual
description: Collect and present all manual tasks that cannot be automated (database migrations, environment variables, external service configuration). Present as a checklist and wait for user confirmation before integration testing begins.
---

# FSE-Manual — Manual Tasks Checklist

Identifies everything that requires human intervention before integration testing can begin. Never executes these tasks automatically. Presents a checklist and blocks on user confirmation (GATE-4).

## Language Requirement

**All user-facing output MUST be in Chinese (Simplified).** This includes all prompts, questions, status banners, error messages, confirmation gates, and progress displays shown to the user. Internal skill instructions may remain in English.

## Hard Constraints

1. **Never execute database scripts automatically.** Display them for user review only.
2. **Never modify environment files directly.** Show what needs to be set and where.
3. **User must confirm all items are done** before state advances.
4. **All user-facing questions and confirmations MUST use `AskUserQuestion` tool.** Never show text prompts expecting free-form reply.

## Step 1 — Mark state

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state MANUAL_TASKS_PENDING
```

## Step 2 — Scan for manual items

Run parallel scans across all backend projects:

```bash
codeagent-wrapper --parallel <<'EOF'
---TASK---
id: scan_manual_<backend_name>
agent: code-explorer
workdir: <backend_path>
---CONTENT---
Scan the recent code changes and identify everything that requires manual human action
before the application can run. Look for:

1. DATABASE MIGRATIONS
   - New tables (extract DDL SQL)
   - Column additions or modifications
   - Index creation
   - Seed data requirements

2. ENVIRONMENT VARIABLES
   - New env vars referenced in code (check application.yml, .env, config files)
   - For each: variable name, purpose, example value, whether required or optional

3. EXTERNAL SERVICE CONFIGURATION
   - New third-party service integrations requiring API keys or setup
   - Webhook registrations needed
   - DNS or CORS configuration changes

4. CACHE / MESSAGE QUEUE
   - New Redis keys or namespaces requiring initialization
   - New Kafka topics or queues to create

5. PERMISSION / ROLE CHANGES
   - New roles or permissions that need to be seeded into the database

Format each item as:
TYPE: <MIGRATION|ENV_VAR|SERVICE|CACHE|PERMISSION>
DESCRIPTION: ...
ACTION_REQUIRED: <exact steps the user must take>
SQL/VALUE: <if applicable>
PRIORITY: REQUIRED | OPTIONAL
EOF
```

## Step 3 — Write manual tasks checklist

Write `.fullstack/tasks/manual-checklist.md`:

```markdown
# Manual Tasks Checklist

Generated: <timestamp>
**All items below must be completed before integration testing.**

---

## 数据库迁移

### Migration 001: Create users table
**Status**: [ ] Pending
**Action**: Execute the following SQL against the development database:

```sql
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(200) UNIQUE NOT NULL,
  status TINYINT DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 环境变量

### ENV: JWT_SECRET
**Status**: [ ] Pending
**Required**: YES
**Purpose**: JWT token signing key
**Where to set**: `<backend_path>/.env` or system environment
**Example value**: `your-256-bit-secret-key-here`
**How to verify**: Application starts without "missing env" error

---

## 外部服务配置

(None identified / list items if found)

---

## 汇总
Total required items: <N>
Total optional items: <N>
```

## Step 4 — Confirmation Gate (GATE-4)

Present to user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GATE-4：人工任务确认
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The following must be completed manually before integration:

[manual-checklist.md content]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full checklist: .fullstack/tasks/manual-checklist.md

请完成上述必填项，然后确认：

  1. 已完成 — 所有必填项均已处理
  2. 跳过可选项 — 必填项已完成，跳过可选内容
  3. 需要帮助 — 说明哪一项不清楚
```

**Use `AskUserQuestion` tool** for this confirmation.

**若选择"已完成"或"跳过可选项"：**
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state MANUAL_TASKS_DONE
```
输出: `<promise>FSE_PHASE_COMPLETE</promise>`

**若选择"需要帮助"：** 详细解释对应项并重新提问。
