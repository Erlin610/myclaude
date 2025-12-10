# ALIN Maint Workflow Module (v3.0)

AI-driven ops automation workflow orchestrated by Claude Code with Codex execution, covering monitoring, release, incident, security, and optimization scenarios. Enforces KISS/YAGNI with **mandatory context loading + UltraThink deep analysis + interactive investigation + command approval**, eliminating hallucinations and destructive automation.

## Core Improvements (v3.0)

### ✅ Four Core Improvements
1. **Mandatory context loading** — every action must load `.alin/ops-context/infra-profile.md`; refuse to continue without the dossier.
2. **Interactive investigation mode** — round-based loop: issue commands → wait for user output → analyze → next round (up to 5), preventing one-shot incorrect plans.
3. **🧠 UltraThink synthesis** (NEW) — comprehensive root cause analysis after investigation, evaluating multiple solution approaches with trade-off analysis before generating commands.
4. **Command approval** — output only the command list plus risk level and rollback; never auto-execute, user runs manually.

## MCP Integration

### Context7 Knowledge Source

ALIN-Maint integrates **Context7 MCP** as the primary knowledge source for real-time technical documentation:

**Coverage (90%+ ops scenarios)**:
- Container orchestration (Kubernetes, Docker)
- Cloud providers (Alibaba Cloud, AWS, GCP)
- Databases & caches (PostgreSQL, Redis, MongoDB)
- Message queues (Kafka, RabbitMQ)
- Monitoring (Prometheus, Grafana)
- CI/CD (GitHub Actions, GitLab CI, ArgoCD)

**Why Context7**:
- ✅ Real-time documentation (no knowledge cutoff issues)
- ✅ Accurate command syntax (avoid hallucination)
- ✅ Version-specific information
- ✅ Best practices and examples

**Fallback Strategy**:
```
Context7 → WebFetch (official docs) → WebSearch → User confirmation
```

**Prerequisites**:
- Context7 MCP server installed and configured
- If unavailable: workflows will fallback to internet search with disclaimer

### 📋 Usage Flow

#### Step 0: Initialize the ops dossier (first use)
```bash
/alin-maint init
```

**Dynamic deep-dive mode** (no round limit until the system is fully understood):

**Phase 1: High-level architecture**
- Cloud platform identification and concrete services (AWS EKS/RDS/ElastiCache…)
- Environment/cluster configuration (prod/staging/dev)
- Service inventory and key-service tagging (multiSelect top 5-10)

**Phase 2: Deep dive into key services** (one by one, 5-8 rounds each)
For each key service collect:
- Basics: tech stack, replica count, resources, ports
- Dependencies: upstream/downstream/data stores
- Config management: ConfigMap/Secret/env vars
- Monitoring: health checks, key metrics + normal ranges, alert rules
- Logging: paths, formats, key fields
- **Common issues**: symptoms + quick triage commands + expected output + fixes (critical)
- Deployment: images, rollout strategy, rollback commands

**Phase 3-5: Monitoring, deployment, security**
- Monitoring tools + dashboard links + log aggregation
- CI/CD + image registry + release process
- Key management + access control + on-call

**Phase 6: Documentation bundle generation** (automated)
- Generate ASCII architecture map
- Generate dependency matrix
- Generate full document bundle (7+ files)

**Produced dossier bundle and documentation structure**:
```
.alin/
├── ops-context/              # Knowledge base (structured operational knowledge)
│   ├── infra-profile.md      # Overview: cloud, clusters, services
│   ├── architecture.md       # ASCII topology + dependency matrix
│   ├── monitoring.md         # Key metrics + normal ranges + alerts
│   ├── services/             # Per-service detailed docs
│   │   ├── api-gateway.md    # Includes common issues + quick triage
│   │   ├── auth-service.md
│   │   └── ...
│   └── runbooks/             # Ops handbooks
│       ├── common-issues.md  # Common issues + fast handling
│       ├── deployment.md     # Deployment process
│       └── rollback.md       # Rollback process
│
├── ops-docs/                 # Runbooks (incident execution logs)
│   ├── 2025-12-09-api-500-error.md
│   ├── 2025-12-10-redis-down.md
│   └── ...
│
└── analysis/                 # Root cause analysis reports (UltraThink output)
    ├── 2025-12-09-memory-leak-investigation.md
    ├── 2025-12-10-latency-spike-analysis.md
    └── ...
```

**How this differs from simple Q&A**:
- ✅ **Dynamic deep-dive**: no fixed round count; keeps asking until the info is complete.
- ✅ **Hands-on focus**: prioritizes common issues and quick triage commands.
- ✅ **Complete doc bundle**: 7+ files including architecture, dependency matrix, and runbooks.
- ✅ **Immediately usable**: when incidents occur, jump to the common-issues section in `services/{service}.md`.

#### Step 1: Ops issue diagnosis
```bash
/alin-maint "K8s pod 重启频繁，需要日志分析"
```

**Workflow** (Enhanced with UltraThink):
1. Auto-load the dossier → output a summary for confirmation.
2. Scenario identification → route to the appropriate specialist agent.
3. **Iterative investigation** (max 5 rounds):
   ```
   Round 1:
   > 请执行：kubectl get pods -n production
   > 目的：确认 pod 状态
   [等待你粘贴输出]

   Round 2: (基于实际输出)
   > 请执行：kubectl describe pod xxx -n production
   [等待你粘贴输出]
   ...
   ```
4. **🧠 UltraThink Synthesis** (NEW - Deep Analysis):
   ```markdown
   ## 🧠 UltraThink Root Cause Analysis

   ### 根本原因
   **主要原因**: Memory leak in application code
   **促成因素**: Increased traffic 3x, no memory limits
   **触发时机**: Gradual accumulation over 48 hours
   **监控盲区**: No alert on memory growth trend

   ### 解决方案评估
   | 方案 | 风险 | 时间 | 持久性 | 影响范围 | 回滚难度 |
   |------|------|------|--------|----------|----------|
   | Restart pods | ✅ | 1min | Hotfix | Single service | Easy |
   | Set memory limits | ⚠️ | 5min | Workaround | Single service | Easy |
   | Fix code leak | 🔴 | 2hr | Permanent | Multiple | Medium |

   ### 推荐方案
   **立即**: Restart pods (restore service)
   **短期**: Set memory limits + monitor (prevent OOM)
   **长期**: Fix memory leak in code (file DEV-789)

   ### 决策理由
   Restart provides immediate relief. Memory limits prevent future OOM.
   Code fix is long-term but non-urgent since workaround is effective.
   ```

   **文档化选项**:
   - If analysis is complex → Ask user: "分析报告较为详细，是否生成文档？"
   - If yes → Save to `.alin/analysis/{date}-{topic}.md`

5. Output a command checklist (based on UltraThink recommendation):
   ```markdown
   ## 📋 Recommended Actions (Based on UltraThink)

   ### Step 1: 立即恢复服务（重启 Pod）
   ```bash
   kubectl rollout restart deployment api-gateway -n production
   ```
   **风险等级**：✅ 安全
   **预期结果**：Pod 重启，内存释放

   ### Step 2: 设置内存限制（防止复发）
   ```bash
   kubectl set resources deployment api-gateway \
     --limits=memory=4Gi --requests=memory=2Gi -n production
   ```
   **风险等级**：⚠️ 中风险
   **回滚方法**：kubectl rollout undo

   ❓ **请确认**：输入 "execute" 继续
   ```

6. Documentation (Three streams):
   - **Analysis report**: `.alin/analysis/{date}-{topic}.md` (if complex)
   - **Runbook**: `.alin/ops-docs/{date}-{topic}.md` (always)
   - **Knowledge base**: `.alin/ops-context/` (if new entities discovered)

## Directory Structure

```
alin-maint-workflow/
├── commands/
│   └── alin-maint.md              # main orchestrator (6-step workflow)
├── agents/
│   ├── maint-init.md         # dossier initialization (NEW)
│   ├── maint-monitor.md      # monitoring analysis
│   ├── maint-deploy.md       # deployment management
│   ├── maint-incident.md     # incident response
│   ├── maint-security.md     # security hardening
│   └── maint-optimize.md     # performance optimization
└── README.md
```

## Agent Overview

| Agent | Color | Responsibility | Typical Output |
|-------|-------|----------------|----------------|
| **maint-init** | 🔷 cyan | Dossier initialization | infra-profile.md (ops architecture dossier) |
| **maint-monitor** | 🔵 blue | Log/metric analysis | Monitoring report + alert rule suggestions |
| **maint-deploy** | 🟢 green | CI/CD + deployment | Pipeline config + deployment script + rollback plan |
| **maint-incident** | 🔴 red | Incident triage | Incident report + root cause + remediation steps |
| **maint-security** | 🟡 yellow | Security audit | Vulnerability scan report + fix PR draft |
| **maint-optimize** | 🟣 purple | Performance/cost optimization | Bottleneck analysis + optimization plan + benefit estimate |

## Usage Examples (kept in Chinese for clarity)

### 监控场景
```bash
/alin-maint "Grafana 告警 CPU 使用率过高，需要分析"
```
→ maint-monitor 迭代调查：
1. Round 1: 查看当前 CPU 指标
2. Round 2: 分析 top 进程
3. Round 3: 检查资源限制
4. 输出：告警规则建议 + 优化命令

### 部署场景
```bash
/alin-maint "为 api-service 生成 GitHub Actions 部署到 staging"
```
→ maint-deploy 迭代生成：
1. Round 1: 查看现有 workflow
2. Round 2: 确认镜像仓库
3. 输出：CI/CD 配置 + 部署脚本 + 回滚命令

### 故障场景
```bash
/alin-maint "服务返回 500 错误，影响 20% 用户"
```
→ maint-incident 快速响应：
1. Round 1: Triage - 服务状态 + 错误日志
2. Round 2-3: 根因定位
3. 输出：缓解措施 + 根治方案 + 预防措施

### 安全场景
```bash
/alin-maint "npm audit 发现 3 个 Critical 漏洞"
```
→ maint-security 扫描分析：
1. Round 1: 执行完整扫描
2. Round 2: 分级漏洞
3. 输出：修复 PR 草案 + 测试命令

### 优化场景
```bash
/alin-maint "API 延迟 p99 从 100ms 升到 500ms"
```
→ maint-optimize 性能分析：
1. Round 1: 基线确认
2. Round 2-3: 瓶颈定位
3. 输出：优化方案 + 预期收益 + 灰度策略

## Architecture (ASCII)

```
alin-maint-workflow (v3.0)
|
|-- /alin-maint init (first use)
|   |-- Dynamic deep-dive Q&A to collect ops architecture
|   `-- generate .alin/ops-context/infra-profile.md
|
`-- /alin-maint "问题描述" (daily use)
    |
    |-- Step 0: Context Loading (mandatory)
    |   |-- load infra-profile.md
    |   `-- output dossier summary for confirmation
    |
    |-- Step 1: Scenario Identification
    |   `-- AskUserQuestion + options based on dossier
    |
    |-- Step 2: Information Gathering (read-only)
    |   `-- Read/Grep/Bash to collect required data
    |
    |-- Step 3: Iterative Investigation
    |   |-- Round 1: propose 1-3 commands → wait for user output
    |   |-- Round 2-5: iterate based on actual output
    |   `-- summarize findings + next-step hypothesis each round
    |
    |-- Step 4: UltraThink Synthesis (NEW in v3.0)
    |   |-- Evidence consolidation + multi-perspective analysis
    |   |-- Root cause identification + solution evaluation
    |   |-- Trade-off analysis + decision synthesis
    |   `-- Documentation decision (save to .alin/analysis/ if complex)
    |
    |-- Step 5: Solution Generation (COMMAND-ONLY)
    |   |-- command checklist + risk levels + rollback methods
    |   `-- explicitly note: do not auto-execute
    |
    `-- Step 6: Documentation
        |-- Analysis report -> .alin/analysis/ (if approved in Step 4)
        |-- Runbook -> .alin/ops-docs/ (always)
        `-- Knowledge base updates -> .alin/ops-context/ (incremental)
```

## Safety Principles

### Three risk levels
- ✅ **Level 1 (read-only)**: kubectl get/describe/logs, cat, ps, etc. → safe to run directly.
- ⚠️ **Level 2 (confirmation required)**: kubectl apply/scale, systemctl restart → type "execute" to confirm.
- 🔴 **Level 3 (dangerous)**: kubectl delete, rm -rf, DROP DATABASE → retype the full command for second confirmation.

### Mandatory rules
1. **Context first** — refuse to proceed without `infra-profile.md` to avoid hallucinations.
2. **Iterative investigation** — max 3 commands per round, max 5 rounds to avoid loops.
3. **Command approval** — commands are output only; never auto-executed.
4. **Reversibility** — every change must include a rollback path.

## Best Practices

1. **Initialize the dossier first**
   ```bash
   /alin-maint init  # 首次使用，5 分钟建立档案
   ```

2. **Keep the dossier fresh**
   ```bash
   /alin-maint init  # 新增服务、环境变更后重新运行
   ```

3. **Execute commands in stages**
   - Run read-only commands first (✅ safe)
   - After confirming impact, run change commands (⚠️ confirmation required)
   - Think twice before dangerous steps (🔴 high risk)

4. **Validate every step**
   - Paste full output after running commands
   - Adjust next steps based on real results
   - No skipping, no assumptions

5. **Persist runbooks**
   - All actions auto-archive to `.alin/ops-docs/`
   - Reuse the same runbooks for similar issues

## ⚡ 快速定位能力（真实运维场景）

**场景 1：凌晨 2 点收到 P1 告警 - API 500 错误率飙升**
```bash
/alin-maint "api-gateway 返回 500 错误，影响 30% 用户"
```
1. **立即加载** `services/api-gateway.md` 的常见问题章节
2. **快速定位**：
   - 查看 "Issue 1: High Error Rate" → 症状匹配
   - 执行诊断命令：`kubectl logs api-gateway-xxx -n production | grep "ERROR"`
   - 看到输出：大量 "connection timeout to Redis"
3. **立即解决**：
   - 查看 `services/api-gateway.md` 的依赖章节 → Redis (cache)
   - 查看 `runbooks/common-issues.md` → "Database Connection Pool Exhausted"
   - 执行缓解命令：`kubectl scale deployment api-gateway --replicas=8`
   - **5 分钟内恢复服务**

**场景 2：部署新版本后发现内存泄漏**
```bash
/alin-maint "auth-service 部署后内存持续增长"
```
1. **加载** `services/auth-service.md`
2. **常见问题章节** → "Issue 2: Memory Leak"
3. **快速诊断**：
   - 执行：`kubectl top pod auth-service-xxx`
   - 确认内存从 1Gi → 3.5Gi → 持续增长
4. **立即回滚**：
   - 查看部署章节 → 回滚命令
   - 执行：`kubectl rollout undo deployment/auth-service -n production`
   - **3 分钟内回滚完成**

**场景 3：数据库连接池耗尽**
```bash
/alin-maint "大量 connection timeout 错误"
```
1. **从 `runbooks/common-issues.md`** 查找 "Connection Pool"
2. **快速定位命令**：
   ```bash
   psql -h db-host -c "SELECT count(*) FROM pg_stat_activity;"
   kubectl logs api-gateway-xxx | grep "ECONNREFUSED"
   ```
3. **立即缓解** + 根治：
   - 临时：扩容服务副本
   - 排查：检查慢查询
   - 修复：调整连接池配置

**关键区别**：
- ❌ **传统方式**：盲目猜测 → 执行命令 → 发现错误 → 再猜 → 浪费 30 分钟
- ✅ **ALIN-Maint v2.0**：直接查档案 → 常见问题匹配 → 精准命令 → **5 分钟解决**

## Comparison with Previous Versions

| Feature | v1.0 | v2.0 | v3.0 (current) |
|---------|------|------|----------------|
| Context management | ❌ No dossier, guessing | ✅ Mandatory infra-profile.md | ✅ Same + Entity gap detection |
| Investigation style | ❌ One-shot full plan | ✅ Iterative 5 rounds | ✅ Same + UltraThink synthesis |
| Root cause analysis | ❌ No formal analysis | ⚠️ Implicit in investigation | ✅ **Explicit Step 4 UltraThink** |
| Solution evaluation | ❌ Single approach | ⚠️ Best-effort recommendation | ✅ **Multi-approach trade-off matrix** |
| Command execution | ⚠️ Codex auto-executes | ✅ Output only; user runs | ✅ Same + Context7 validation |
| Risk control | ⚠️ Confirm after the fact | ✅ Pre-graded + dual confirmation | ✅ Same |
| Documentation | ❌ No structured docs | ✅ Runbooks (.alin/ops-docs/) | ✅ **3-tier: analysis/runbooks/KB** |
| Workflow steps | 3 steps | 5 steps | **6 steps** (added UltraThink) |

## Installation

```bash
python3 install.py --module alin-maint
```

After installation:
1. Run `/alin-maint init` to initialize the dossier.
2. Use `/alin-maint "问题描述"` to start ops automation.

---

**ALIN-Maint v3.0** — context-driven, UltraThink-powered, interactive, and safety-first ops automation.
