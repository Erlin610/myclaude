# ALIN-Maint Context7 MCP Integration Design

**Created**: 2025-12-09
**Status**: Implementation Ready
**Priority**: P0 (Critical for accuracy)

---

## Core Problem

**Current Issue**: ALIN-Maint agents generate commands and configurations based on:
- Built-in knowledge (subject to model knowledge cutoff)
- User-provided context (may be incomplete)
- Internet search (slow, unreliable, often outdated)

**Risk**: Hallucinated commands, outdated API usage, incorrect configuration syntax.

**Solution**: Integrate Context7 MCP as primary knowledge source for real-time, accurate technical documentation.

---

## Context7 MCP Overview

### What is Context7?
A Model Context Protocol (MCP) server that provides:
- Real-time technical documentation (Kubernetes, Docker, cloud providers)
- API references (REST APIs, CLI tools)
- Configuration schemas (YAML, JSON, TOML)
- Best practices and examples
- Version-specific documentation

### Coverage (Estimated 90%+ for ops scenarios)
1. **Container Orchestration**: Kubernetes API, kubectl syntax, Helm charts
2. **Cloud Providers**: Alibaba Cloud (aliyun), AWS (aws-cli), GCP (gcloud)
3. **Databases**: PostgreSQL, MySQL, Redis, MongoDB configuration
4. **Message Queues**: Kafka, RabbitMQ, NATS
5. **Monitoring**: Prometheus query language (PromQL), Grafana dashboard config
6. **CI/CD**: GitHub Actions, GitLab CI, ArgoCD
7. **Service Mesh**: Istio, Envoy configuration
8. **Infrastructure as Code**: Terraform, Ansible syntax

### Fallback Scenarios (Remaining 10%)
- Proprietary internal tools
- Custom in-house frameworks
- Bleeding-edge unreleased features
- Company-specific configurations

---

## Integration Strategy

### 1. Tool Authorization

**Add to all ALIN-Maint files**:
```yaml
tools: Read, Edit, Write, Bash, Grep, Glob, WebFetch, TodoWrite, mcp__context7
```

**Affected files**:
- `commands/alin-maint.md`
- `agents/alin-maint-init.md`
- `agents/alin-maint-monitor.md`
- `agents/alin-maint-deploy.md`
- `agents/alin-maint-incident.md`
- `agents/alin-maint-security.md`
- `agents/alin-maint-optimize.md`

### 2. Query Trigger Conditions

**When to call Context7** (priority order):

#### P0 - Immediate Query (before outputting commands)
- **Command generation**: Before proposing kubectl/docker/cloud CLI commands
- **Configuration syntax**: When writing YAML/JSON manifests
- **API references**: When checking service endpoints or parameters
- **Error interpretation**: When diagnosing unfamiliar error codes

**Example triggers**:
```
User: "api-gateway 内存占用过高"
→ 需要生成 kubectl top/describe 命令
→ Context7 query: "kubernetes kubectl top pod memory usage command syntax"
→ 使用返回的准确语法生成命令

User: "需要修改 Redis maxmemory-policy"
→ 需要确认配置参数名和有效值
→ Context7 query: "redis maxmemory-policy configuration options"
→ 基于文档给出准确的配置建议
```

#### P1 - Validation Query (after user provides info)
- **Configuration validation**: User provides config, verify syntax correctness
- **Best practices check**: User proposes solution, confirm if it follows best practices
- **Version compatibility**: Check if command/config works with user's version

#### P2 - Enhancement Query (optional, if time permits)
- **Alternative approaches**: Show other ways to solve the problem
- **Performance optimization**: Suggest better configurations

### 3. Query Formulation Strategy

**Query format design**:
```
Context: {cloud_provider} {orchestration} {service_type}
Goal: {what information is needed}
Specifics: {version, environment, constraints}
```

**Examples**:

1. **Command syntax query**:
   ```
   Context: Kubernetes 1.28 kubectl
   Goal: Get pod memory usage command
   Specifics: Need to sort by memory, show top 10
   ```

2. **Configuration parameter query**:
   ```
   Context: Alibaba Cloud ACK (Aliyun Container Service for Kubernetes)
   Goal: HPA (Horizontal Pod Autoscaler) configuration
   Specifics: Target CPU 70%, min 2, max 10 replicas
   ```

3. **Error diagnosis query**:
   ```
   Context: Redis 7.0
   Goal: Explain error "OOM command not allowed when used memory > maxmemory"
   Specifics: Current policy eviction-policy, need solution
   ```

### 4. Fallback Strategy

**Decision tree**:
```
1. Try Context7 query
   ↓
2. Context7 returns valid result?
   Yes → Use result, proceed
   No  ↓
3. Context7 error type?
   - "Not found" → Try WebFetch (official docs)
   - "MCP unavailable" → Try WebSearch
   - "Query too vague" → Refine query, retry once
   ↓
4. Fallback returns valid result?
   Yes → Use result, mark as "not verified by Context7"
   No  ↓
5. Ask user for documentation or proceed with disclaimer
```

**Disclaimer template** (when all queries fail):
```markdown
⚠️ **Knowledge Source Unavailable**

无法通过 Context7 或互联网验证以下信息的准确性：
- {component/service name}
- {specific query}

建议：
1. 手动查阅官方文档：{doc_url if known}
2. 在测试环境验证命令
3. 如有内部 Runbook，优先参考
```

---

## Implementation Plan

### Phase 1: Core Integration (P0)

**Update 7 files** with:

1. **Tool Authorization Section** (after Role, before Workflow):
```markdown
## Tool Authorization & Knowledge Sources

**Context7 MCP Integration**:
- **Primary knowledge source** for technical documentation (90%+ coverage)
- **Query triggers**: Before generating commands, validating configurations, interpreting errors
- **Covered domains**: Kubernetes, Docker, Alibaba Cloud/AWS/GCP, Redis/Kafka/PostgreSQL, Prometheus/Grafana, CI/CD tools
- **Fallback**: If Context7 unavailable or query fails → WebFetch (official docs) → WebSearch → Disclaimer

**Query Strategy**:
- Always query Context7 before proposing kubectl/docker/cloud CLI commands
- Validate configuration syntax against real documentation
- Check error codes and diagnostic commands for accuracy
- Prefer real-time docs over model's built-in knowledge (avoid hallucination)

**Usage Examples**:
```markdown
# Example 1: Command generation
User mentions: "查看 pod 日志"
→ Context7 query: "kubernetes kubectl logs command syntax tail follow"
→ Output: `kubectl logs {pod-name} -n {namespace} --tail=100 -f`

# Example 2: Configuration validation
User provides: Redis maxmemory-policy设置
→ Context7 query: "redis maxmemory-policy valid options"
→ Confirm: allkeys-lru, volatile-lru, allkeys-random, etc.

# Example 3: Cloud service API
User asks: "阿里云 ACK 集群扩容"
→ Context7 query: "alibaba cloud ack kubernetes cluster scale nodes aliyun cli"
→ Output: `aliyun cs ScaleOutCluster --cluster-id {id} --count {N}`
```
```

2. **Workflow Integration Points**:

For **alin-maint.md** (orchestrator):
```markdown
**Step 3: Iterative Investigation (enhanced)**
- Per round, propose 1-3 diagnostic commands:

  **NEW: Command Accuracy Check**:
    - Before outputting commands → Query Context7 for syntax validation
    - Query format: "{tool} {action} command syntax {specifics}"
    - Example: "kubectl get pods filtered by label command syntax"
    - If Context7 returns result → Use verified syntax
    - If Context7 unavailable → Use best effort + add disclaimer
```

For **alin-maint-init.md**:
```markdown
**Phase 2: Service Deep Dive**
- Round 4: Monitoring Metrics

  **NEW: Metrics Query Validation**:
    - When user mentions monitoring tool (Prometheus/Grafana) → Query Context7
    - Query: "{tool} query syntax {metric_type}"
    - Example: "prometheus promql query pod memory usage"
    - Use returned query syntax in documentation
```

For **alin-maint-monitor.md**:
```markdown
**Workflow Round 1: Alert Investigation**
- Before proposing diagnostic commands:

  **NEW: Context7 Query**:
    - Query monitoring tool documentation for accurate query syntax
    - Example: "grafana dashboard query prometheus pod cpu usage"
    - Validate metric names and aggregation functions
```

For **alin-maint-deploy.md**:
```markdown
**Workflow Round 2: Deployment Strategy**
- Before generating deployment manifests:

  **NEW: Context7 Query**:
    - Query CI/CD tool configuration syntax
    - Example: "github actions workflow kubernetes deployment kubectl"
    - Query cloud provider deployment APIs
    - Example: "alibaba cloud ack deployment rolling update api"
```

For **alin-maint-incident.md**:
```markdown
**Workflow Round 1: Error Analysis**
- After user provides error message:

  **NEW: Context7 Query**:
    - Query error code documentation
    - Example: "kubernetes pod crashloopbackoff exit code 137 meaning"
    - Query diagnostic commands
    - Example: "kubectl debug pod commands"
```

For **alin-maint-security.md**:
```markdown
**Workflow Round 1: Vulnerability Scan**
- Before suggesting security tools:

  **NEW: Context7 Query**:
    - Query security scanning tool syntax
    - Example: "trivy vulnerability scan docker image command"
    - Query cloud provider security policies
    - Example: "alibaba cloud security group rules aliyun cli"
```

For **alin-maint-optimize.md**:
```markdown
**Workflow Round 1: Performance Analysis**
- Before proposing optimization commands:

  **NEW: Context7 Query**:
    - Query performance profiling tools
    - Example: "kubernetes resource usage analysis kubectl top"
    - Query optimization configurations
    - Example: "redis performance tuning parameters"
```

### Phase 2: README Documentation (P1)

**Update `alin-maint-workflow/README.md`**:

Add section after "Core Improvements":
```markdown
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
```

### Phase 3: Configuration Template (P2)

**Create `.claude/mcp-config-example.json`** (for user reference):
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "env": {
        "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
      }
    }
  }
}
```

---

## Quality Assurance

### Testing Checklist

**Test scenarios**:
1. ✅ Generate kubectl command with Context7 available
2. ✅ Generate kubectl command with Context7 unavailable (fallback)
3. ✅ Validate Redis config with Context7
4. ✅ Query Alibaba Cloud ACK API syntax
5. ✅ Interpret Kubernetes error with Context7
6. ✅ Generate Prometheus query with Context7

**Expected behaviors**:
- Commands use real documentation syntax
- Configurations match official schemas
- Error interpretations reference official docs
- Fallback gracefully when Context7 unavailable

### Metrics

**Success indicators**:
- Command accuracy rate: >95% (validated against official docs)
- Hallucination reduction: >80% (compared to baseline without Context7)
- Query success rate: >90% (Context7 returns valid results)
- Fallback frequency: <10% (most queries handled by Context7)

---

## Risk Mitigation

### Risk 1: Context7 MCP Unavailable
**Mitigation**: Multi-layer fallback (WebFetch → WebSearch → Disclaimer)

### Risk 2: Query Returns Outdated Info
**Mitigation**: Always include version context in queries (e.g., "Kubernetes 1.28")

### Risk 3: Query Too Slow
**Mitigation**: Set timeout (5s), fallback if exceeded

### Risk 4: User Has No Context7 Access
**Mitigation**: Workflow still functional with fallback; add setup instructions in README

---

## Implementation Checklist

**Phase 1 (Critical)**:
- [ ] Update 7 MD files with tool authorization section
- [ ] Add Context7 query points in workflows
- [ ] Add fallback logic in command generation steps
- [ ] Add disclaimer template for unavailable scenarios

**Phase 2 (Important)**:
- [ ] Update README.md with MCP integration section
- [ ] Add usage examples in each agent's Output Format

**Phase 3 (Nice-to-have)**:
- [ ] Create MCP config example
- [ ] Add troubleshooting section in README

---

## Example Query Flow

**Scenario**: User reports "api-gateway pod OOMKilled"

```
1. alin-maint-incident agent receives problem
   ↓
2. Before proposing diagnostic commands:
   Query Context7:
   "kubernetes pod oomkilled diagnosis commands"
   ↓
3. Context7 returns:
   - kubectl describe pod (check memory limits)
   - kubectl top pod (check actual usage)
   - kubectl logs --previous (check last logs before crash)
   ↓
4. Agent outputs verified commands:
   ```bash
   # 1. Check memory limits and requests
   kubectl describe pod api-gateway-xxx -n production | grep -A 5 "Limits\|Requests"

   # 2. Check actual memory usage before crash
   kubectl top pod api-gateway-xxx -n production

   # 3. Check logs before OOM
   kubectl logs api-gateway-xxx -n production --previous --tail=100
   ```
   ↓
5. User executes commands, provides output
   ↓
6. Agent analyzes output, queries Context7 again:
   "kubernetes increase pod memory limit deployment"
   ↓
7. Agent proposes solution with verified syntax:
   ```bash
   kubectl set resources deployment api-gateway \
     --limits=memory=4Gi \
     --requests=memory=2Gi \
     -n production
   ```
```

**Result**: All commands are accurate, user-executable, risk-free.

---

## Conclusion

Context7 integration transforms ALIN-Maint from a "best-effort guesser" to a "documentation-backed expert":

**Before Context7**:
- "Try this command: `kubectl logs pod-name` (syntax may vary)"
- Risk of hallucinated flags or outdated syntax

**After Context7**:
- "Execute this verified command: `kubectl logs api-gateway-xxx -n production --tail=100 -f`"
- Confidence in accuracy, reduced debugging time

**Next Step**: Implement Phase 1 updates to all 7 files.
