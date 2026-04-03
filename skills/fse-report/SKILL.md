---
name: fse-report
description: Generate the final delivery report after all testing passes. Covers what was changed (per project), configuration additions, SQL scripts to execute, and deployment order for frontend and backend projects. Produces DELIVERY-REPORT.md in the workspace root.
---

# FSE-Report — Delivery Report Generator

Produces a complete, actionable delivery report by reading all `.fullstack/` artifacts and
running git diff on each project. Called automatically after `fse-test` completes.

## Language Requirement

**All user-facing output MUST be in Chinese (Simplified).** This includes all prompts, questions, status banners, error messages, confirmation gates, and progress displays shown to the user. Internal skill instructions may remain in English.

## Hard Constraints

1. **Report is generated from facts, not recollection** — every claim must be sourced from
   git diff, workspace.json, manual-checklist.md, or contracts.
2. **All SQL must appear verbatim** — copy exact DDL/DML, no paraphrasing.
3. **Deployment steps must be ordered and numbered** — no ambiguity about sequence.
4. **If a section has no content, write "None" — never omit a section.**

## Step 1 — Collect changed files per project

For each registered project (all types, all in scope):

```bash
codeagent-wrapper --parallel <<'EOF'
---TASK---
id: diff_<type>_<name>
agent: code-explorer
workdir: <project_path>
---CONTENT---
Generate a structured change summary for this project.

1. Run: git diff <base_branch>...<feature_branch> --stat
   List every changed file with: path | +added -removed | action (NEW/MODIFIED/DELETED)

2. Run: git log <base_branch>...<feature_branch> --oneline
   List all commits on the feature branch.

3. For each NEW file: one-line description of its purpose.
4. For each MODIFIED file: one-line description of what changed.
5. For each DELETED file: one-line description of why it was removed.

Output format:
CHANGED_FILES:
  src/views/UserList.vue | +120 -0 | NEW | User list page component
  src/api/user.ts        | +45 -3  | MODIFIED | Added user query and create API calls

COMMITS:
  abc1234 feat: add user list page
  def5678 feat: add user create modal

---TASK---
id: diff_<type>_<name2>
...
EOF
```

## Step 2 — Collect configuration requirements

Read `.fullstack/tasks/manual-checklist.md`.

Extract:
- All **ENV VAR** items → configuration additions
- All **EXTERNAL SERVICE** items → external setup requirements
- All **PERMISSION/ROLE** items → data setup requirements

Also scan each project for any new config keys added during development:

```bash
codeagent-wrapper --parallel <<'EOF'
---TASK---
id: config_scan_<name>
agent: code-explorer
workdir: <project_path>
---CONTENT---
Scan for new configuration keys introduced by the feature branch changes.

Compare <base_branch> vs <feature_branch>:
1. New entries in application.yml / application.properties / .env.example
2. New environment variable references in code (process.env.X, System.getenv("X"), os.environ["X"])
3. New feature flags or toggle keys

For each new config key:
  KEY: <name>
  PURPOSE: <what it does>
  REQUIRED: yes | no
  DEFAULT: <default value or "none">
  EXAMPLE: <example value>
  WHERE: <file to set it in>
EOF
```

## Step 3 — Collect SQL scripts

Read `.fullstack/tasks/manual-checklist.md` for all MIGRATION items.

Also scan backend projects for any migration files added:

```bash
codeagent-wrapper --agent code-explorer - <backend_path> <<'EOF'
Find all database migration scripts introduced in the feature branch.

Check:
- Flyway migrations: src/main/resources/db/migration/V*.sql
- Liquibase changesets
- Any .sql files added or modified in the feature branch
- MyBatis mapper XML files with new DDL statements

For each migration found:
  FILE: <path>
  TYPE: DDL (table/index/column changes) | DML (data inserts/updates)
  DESCRIPTION: <one-line summary>
  SQL: <full content of the script>
  EXECUTION_ORDER: <number, starting from 1>
  CAN_ROLLBACK: yes | no
  ROLLBACK_SQL: <if yes, the rollback statement>
EOF
```

## Step 4 — Determine deployment plan

Read from `workspace.json`:
- All registered frontend projects: name, path, tech_stack, start_cmd, port
- All registered backend projects: name, path, tech_stack, start_cmd, startup_args, startup_env, port

```bash
codeagent-wrapper --parallel <<'EOF'
---TASK---
id: deploy_plan_fe_<name>
agent: code-explorer
workdir: <frontend_path>
---CONTENT---
Determine the deployment procedure for this frontend project.

1. BUILD COMMAND: What command produces the production build?
   (e.g. npm run build, yarn build, pnpm build)
2. OUTPUT DIRECTORY: Where does the build output go?
   (e.g. dist/, build/, .output/)
3. ENVIRONMENT VARIABLES NEEDED AT BUILD TIME:
   List any env vars that must be set before running the build command.
   (e.g. VITE_API_BASE_URL, REACT_APP_API_URL)
4. STATIC ASSET HOSTING: Is this served by Nginx, CDN, or a Node server?
5. CACHE INVALIDATION: Are there any cache-busting steps needed after deployment?

---TASK---
id: deploy_plan_be_<name>
agent: code-explorer
workdir: <backend_path>
---CONTENT---
Determine the deployment procedure for this backend service.

1. BUILD COMMAND: What command packages the application for production?
   (e.g. mvn clean package -DskipTests, gradle bootJar, pip install + freeze)
2. ARTIFACT: What is the output file? (e.g. target/app.jar, dist/app.py)
3. START COMMAND (production): Full command including all required JVM args and flags
   Reference startup_args from workspace.json.
4. HEALTH CHECK: URL to verify the service is running after deployment.
5. DEPENDENCIES: Does this service need other services to be running first?
   (e.g. "requires user-service to be running")
6. ROLLBACK PROCEDURE: How to revert if the deployment fails?
EOF
```

Also read `.fullstack/tests/final-report.md` for Section 8 (Testing Evidence).

## Step 5 — Write DELIVERY-REPORT.md

Write the complete report to `DELIVERY-REPORT.md` in the workspace root:

```markdown
# Delivery Report

**Feature**: <feature_name from requirements>
**Mode**: <full|backend|frontend|frontend-ext|lite>
**Generated**: <timestamp>
**Workspace**: <workspace_id>

---

## 1. Feature Summary

<2-3 paragraph summary of what was built, derived from confirmed.md>

**Requirements covered**: FR-001, FR-002, ...
**API endpoints added**: <N>
**Test cases passed**: <N>/<N>

---

## 2. Changed Files

### Frontend: <project_name>  (`<feature_branch>`)

| File | Change | Description |
|------|--------|-------------|
| src/views/UserList.vue | NEW +120 | User list page with search and pagination |
| src/api/user.ts | MODIFIED +45 -3 | Added user query and create API calls |

**Commits**:
```
abc1234 feat: add user list page
def5678 feat: add user create modal
```

### Backend: <project_name>  (`<feature_branch>`)

| File | Change | Description |
|------|--------|-------------|
| UserController.java | NEW +89 | REST endpoints for user CRUD |
| UserService.java | NEW +120 | Business logic for user management |
| UserMapper.xml | NEW +45 | MyBatis SQL mappings |

**Commits**:
```
789abcd feat: implement user query endpoint
012efgh feat: implement user create endpoint
```

---

## 3. Configuration Changes

### New Environment Variables

| Variable | Required | Purpose | Where to Set | Example Value |
|----------|----------|---------|--------------|---------------|
| `JWT_SECRET` | YES | JWT signing key | `.env` / system env | `your-256-bit-secret` |
| `NACOS_NAMESPACE` | YES | Nacos config namespace | `.env` / system env | `dev` |
| `EMAIL_ENABLED` | NO | Toggle email notifications | `.env` | `true` |

### New Application Config Keys

| Key | File | Default | Description |
|-----|------|---------|-------------|
| `app.user.max-page-size` | application.yml | `100` | Max records per page |

> **Action required**: Add the above variables to the deployment environment before starting the service.

---

## 4. SQL Scripts

> **Execution order matters. Run in the numbered sequence below.**
> **Run against the TARGET environment database before deploying the application.**

### Script 1: Create users table  (DDL — REQUIRED)

```sql
CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(200) UNIQUE NOT NULL,
  status TINYINT DEFAULT 1 COMMENT '1=active 0=disabled',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**Can rollback**: YES
**Rollback SQL**: `DROP TABLE IF EXISTS users;`

---

### Script 2: Seed default roles  (DML — REQUIRED)

```sql
INSERT IGNORE INTO roles (code, name, created_at)
VALUES ('USER_ADMIN', '用户管理员', NOW());
```

**Can rollback**: YES
**Rollback SQL**: `DELETE FROM roles WHERE code = 'USER_ADMIN';`

---

## 5. Deployment Plan

### Pre-deployment Checklist

- [ ] All SQL scripts in Section 4 executed successfully
- [ ] All required environment variables in Section 3 configured
- [ ] Feature branches merged to target branch (or deployment from feature branch confirmed)
- [ ] Downstream teams notified of new API endpoints (see Section 6)

### Backend Deployment

**Deploy order** (if multiple backend services, order matters):

#### Step 1 — <backend_project_name>

```bash
# 1. Build
mvn clean package -DskipTests

# 2. Stop existing instance (if running)
# (procedure depends on deployment platform)

# 3. Start
java -jar target/app.jar \
  -Dspring.profiles.active=prod \
  -Dlocal_name=<node_identity> \
  -Dnacos.config.namespace=<prod_namespace>

# 4. Verify health
curl http://localhost:8080/actuator/health
# Expected: {"status":"UP"}
```

**Rollback**: redeploy previous jar from artifact repository.

---

### Frontend Deployment

#### Step 1 — <frontend_project_name>

```bash
# 1. Set build-time environment variables
export VITE_API_BASE_URL=https://api.production.com
export VITE_APP_VERSION=$(git rev-parse --short HEAD)

# 2. Build
npm run build
# Output: dist/

# 3. Deploy dist/ to hosting
# (rsync to server / upload to CDN / copy to Nginx root)
rsync -avz dist/ user@server:/var/www/<app_name>/

# 4. Clear CDN cache (if applicable)
# (procedure depends on CDN provider)
```

**Rollback**: redeploy previous dist/ from last successful build artifact.

---

## 6. API Changes (for downstream consumers)

> Share this section with any team consuming these APIs.

### New Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | /api/users | Bearer | List users with pagination |
| POST | /api/users | Bearer | Create a new user |
| GET | /api/users/{id} | Bearer | Get user detail |

Full spec: `.fullstack/contracts/openapi.yaml`
Integration guide: `.fullstack/contracts/api-integration-guide.md`

---

## 7. Known Issues & Limitations

<list from open issues in workspace.json, or "None">

---

## 8. Testing Evidence

| Test ID | Name | Result | Mode |
|---------|------|--------|------|
| TC-001 | User list renders | PASS | browser |
| TC-002 | Empty state shown | PASS | browser |
| TC-BE-001 | GET /api/users returns 200 | PASS | api |

Full test report: `.fullstack/tests/final-report.md`
```

## Step 6 — Advance state to COMPLETED

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state COMPLETED
python "$HOME/.claude/skills/fse/scripts/workspace.py" session-end
python "$HOME/.claude/skills/fse/scripts/workspace.py" progress
```

Output:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
交付报告已生成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DELIVERY-REPORT.md 已写入工作区根目录。

关键数据：
  变更文件数    ：<N>（前端）+ <N>（后端）
  SQL 脚本     ：<N>（部署前须执行）
  配置变更     ：<N> 个新变量
  API 接口     ：<N> 个新增

请将 DELIVERY-REPORT.md 分享给：
  → 运维团队    （第 3、4、5 节）
  → 前端团队    （第 5 节 — 前端部署）
  → 下游 API 使用方（第 6 节）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<promise>FSE_COMPLETE</promise>
```
