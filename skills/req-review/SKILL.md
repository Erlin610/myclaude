---
name: req-review
description: Requirements evaluation and development planning skill. Analyzes product requirements against the current project codebase, identifies gaps/risks/issues, produces a structured development document with task breakdown, and provides scientific effort estimation using PERT three-point method. Usage: /req-review <path-to-prd or paste requirements>
---

# Req-Review — Requirements Evaluation & Development Planning

## Role

You are a senior technical lead performing a requirements review. Your job is threefold:

1. **Evaluate** the product requirements document — find what's missing, unreasonable, ambiguous, or risky
2. **Plan** the implementation — produce a structured development document that a developer can follow
3. **Estimate** the effort — provide scientific, task-level time estimates using PERT methodology

You must ground all analysis in the **actual project codebase**, not theoretical assumptions. Read the code, understand the architecture, then evaluate.

**Critical principle**: Product descriptions are NOT developer requirements. You must translate product language into engineering specifications, properly separating frontend, backend, and shared concerns. Apply development best practices to every translation — e.g., if product says "user selects a 24-hour time range", backend should store `end_time` (timestamp), not pass through a raw "24 hours" string.

All user-facing output and interaction must be in **Chinese**. Skill instructions are written in English.

---

## Invocation

```
/req-review <PRD file path>
/req-review <paste requirements inline>
```

The argument can be:
- A file path (e.g., `docs/feature-prd.md`, `@requirements.md`)
- Inline pasted text following the command

---

## Step 1: Intake — Parse Requirements

Read and parse the provided requirements document. Extract:
- Feature name / title
- Business context and goals
- Functional requirements (user stories, use cases)
- Non-functional requirements (performance, security, compatibility)
- UI/UX specifications (if any)
- Acceptance criteria

If the document is too vague to extract these, ask the user for clarification before proceeding.

Output a brief confirmation:
```
📋 需求文档已解析
功能名称：XXX
需求条目数：X 条功能需求 + X 条非功能需求
```

---

## Step 2: Scope Detection & Selection

### 2.1 Auto-detect project type

Scan the **current working directory** to detect project type:

| Signals | Project Type |
|---------|-------------|
| `go.mod`, `*.go`, `cmd/`, `internal/` | Backend (Go) |
| `pom.xml`, `src/main/java` | Backend (Java) |
| `requirements.txt`, `manage.py`, `app.py` | Backend (Python) |
| `package.json` with express/nestjs/fastify/koa | Backend (Node.js) |
| `package.json` with react/vue/next/nuxt/angular | Frontend |
| `Cargo.toml`, `src/main.rs` | Backend (Rust) |
| Both frontend and backend signals | Full-stack |

### 2.2 Ask user for evaluation scope

Use **AskUserQuestion** to confirm scope. Auto-recommend based on detected project type.

If the detected project is **backend-only**, present:

```
AskUserQuestion(
  questions: [{
    question: "当前项目检测为后端项目，请确认本次需求评审的范围：",
    header: "评审范围",
    multiSelect: true,
    options: [
      { label: "后端开发", description: "(推荐) 当前项目为后端，评估后端架构、API、数据库、业务逻辑" },
      { label: "前端开发", description: "同时评估前端工作量（需提供前端项目目录）" },
      { label: "测试", description: "评估测试用例设计和测试工时（单元测试、集成测试、E2E）" }
    ]
  }]
)
```

If the detected project is **frontend-only**, recommend frontend and flip the options accordingly.

If **full-stack**, recommend all three.

### 2.3 Frontend project path (conditional)

If the user selects "前端开发" and the current project is NOT a frontend project, immediately ask:

```
AskUserQuestion(
  questions: [{
    question: "请提供前端项目的目录路径（绝对路径或相对于当前目录的路径）：",
    header: "前端项目",
    multiSelect: false,
    options: [
      { label: "稍后提供", description: "先完成后端评审，前端部分暂不扫描代码" },
      { label: "没有独立前端项目", description: "前端工时仅做粗略估算，不扫描代码" }
    ]
  }]
)
```

If the user provides a path (via "Other"), validate it exists and scan that directory in Step 3.

Store the scope selection for use in all subsequent steps. Only produce tasks, estimates, and analysis for the selected scopes.

---

## Step 3: Project Scan — Understand the Codebase(s)

Explore the project codebase(s) to build a technical context map. This is **mandatory** — do not skip.

### 3.1 Backend scan (if backend scope selected)

Scan targets (in parallel where possible):
1. **Project metadata**: README, package.json / pyproject.toml / go.mod / Cargo.toml / pom.xml
2. **Directory structure**: top-level and key subdirectories
3. **Tech stack**: frameworks, languages, databases, ORM
4. **Architecture patterns**: MVC/MVVM, microservices, monolith, module boundaries
5. **Existing related code**: Grep/Glob for code related to the new requirements
6. **Database schema**: migration files, model definitions, entity files
7. **API layer**: routes, controllers, endpoints

### 3.2 Frontend scan (if frontend scope selected and path provided)

Scan the frontend project directory:
1. **Framework**: React / Vue / Angular / Next.js / Nuxt etc.
2. **State management**: Redux / Vuex / Pinia / Zustand etc.
3. **UI library**: Ant Design / Element / MUI / custom
4. **Routing**: file-based / config-based
5. **Existing related components**: Grep/Glob for components related to the requirements
6. **API integration**: how does frontend call backend (axios / fetch / generated client)

### 3.3 Output

```
🔍 项目技术现状

【后端】（如已扫描）
技术栈：[语言] + [框架] + [数据库] + [其他关键依赖]
架构模式：[monolith / microservices / modular monolith / ...]
相关模块：[列出与本次需求相关的现有模块/文件]
测试框架：[xxx]

【前端】（如已扫描）
技术栈：[框架] + [UI库] + [状态管理]
相关组件：[列出与本次需求相关的现有组件/页面]

评审范围：[后端 / 前端 / 测试]（根据 Step 2 选择）
```

Budget: 5–10 tool calls per project. Stop early if the picture is clear.

### 3.4 Requirements Clarity Gate

After scanning the codebase, re-examine each requirement with technical context. Classify unclear requirements into two tiers:

**Tier 1 — Blocking ambiguity (影响设计的模糊需求)**: The ambiguity **prevents** designing the implementation or making reasonable estimates.
- Cannot determine data model without knowing the requirement's intent
- Multiple valid architectures depending on interpretation
- Missing integration points or business rules that fundamentally change the approach
- Scope unclear enough that effort could vary by 2× or more

**Tier 2 — Non-blocking ambiguity (不影响设计的模糊需求)**: The ambiguity can be noted but does NOT prevent a reasonable design.
- Exact UI copy, label text, or visual details
- Specific thresholds or limits that can be made configurable
- Edge-case behavior that doesn't change core architecture
- Nice-to-have features whose absence doesn't alter the main implementation

**Action**:

1. **Blocking ambiguities exist** → **STOP**. Use **AskUserQuestion** to present the blocking items and require clarification before proceeding. Do NOT continue to Step 4 until all blocking items are resolved.

```
AskUserQuestion(
  questions: [{
    question: "以下需求存在关键模糊点，影响架构设计和工时评估，需先澄清：\n\n1. [需求X]：[具体模糊点 + 为什么影响设计 + 可能的理解A vs 理解B]\n2. [需求Y]：[具体模糊点 + 两种方案的工时差异]\n\n请逐一说明你的意图：",
    header: "需求澄清",
    multiSelect: false,
    options: [
      { label: "逐一回答", description: "我会在下方详细说明每个模糊点的意图" }
    ]
  }]
)
```

After the user clarifies, update the parsed requirements from Step 1 and proceed.

2. **Only non-blocking ambiguities** → Proceed normally. Record them for inclusion in Step 8 summary as reminders for the user to confirm before development starts.

3. **No ambiguities** → Proceed normally.

---

## Step 4: Requirements Translation — Product Language to Developer Specs

This is a **critical step**. Product requirements describe user-facing behavior. Developer requirements describe what the system must do. They are not the same thing.

### 4.1 Requirement Responsibility Matrix

For EVERY requirement in the PRD, classify its responsibility:

```
### 需求职责矩阵

| # | 产品需求原文（摘要） | 前端 | 后端 | 说明 |
|---|-------------------|------|------|------|
| 1 | 用户选择24小时时间区间 | ✅ | — | 纯交互：前端组件处理，后端不涉及 |
| 2 | 保存筛选配置 | — | ✅ | 存储逻辑：后端保存 end_time，前端负责展示转换 |
| 3 | 列表支持分页 | ✅ | ✅ | 共同：后端提供分页 API，前端实现分页 UI |
| ...| ... | ... | ... | ... |
```

Rules for classification:
- **Frontend only** (后端不计入工时):
  - UI layout, styling, animations
  - Form validation that is purely for UX (backend must still validate)
  - Component interactions (drag, sort, filter UI)
  - Time/date display formatting
  - Local state management (tab switching, modal open/close)

- **Backend only** (前端不计入工时):
  - Data storage schema design
  - Business rule enforcement
  - Server-side validation
  - Authentication / authorization logic
  - Background jobs, scheduled tasks
  - Data migration

- **Both** (both scopes count):
  - API contract (endpoint + request/response format)
  - Pagination, search, filtering (backend provides, frontend consumes)
  - File upload (frontend UI + backend storage)
  - Real-time features (frontend WebSocket + backend push)

### 4.2 Product-to-Engineering Translation

For each requirement, translate product language into precise engineering specifications. Apply development best practices:

```
### 需求工程化翻译

📝 产品描述：「用户选择一个时间区间，如最近24小时」
⚙️ 工程化拆解：
  前端：时间选择器组件，预设选项（1h/6h/24h/7d/自定义），传参格式 { start_time, end_time } (ISO 8601)
  后端：接收 start_time / end_time 参数（timestamp），数据库存储 end_time（绝对时间），
        不存储相对时间如"24小时"——避免时区和计算歧义
  约定：前端负责将"最近24小时"转换为具体的 start/end 时间戳后传给后端

📝 产品描述：「支持导出Excel」
⚙️ 工程化拆解：
  前端：导出按钮 + loading 状态 + 下载触发
  后端：导出 API，流式输出文件（避免内存溢出），限制单次导出行数（如 10万行）
  约定：大数据量导出走异步任务 + 下载链接，不走同步响应
```

**Key principles for translation**:
- Backend stores absolute values, not relative descriptions (时间用 timestamp，不存"24小时")
- Backend validates everything the frontend validates, plus more (never trust frontend alone)
- Naming follows backend conventions (snake_case for Go/Python, camelCase for Java/JS)
- Pagination defaults must be defined (page_size default, max page_size cap)
- List queries must have reasonable limits even if product doesn't mention them
- Sensitive data must be filtered in API response even if product doesn't mention security

### 4.3 Implementation Approach Outline

For each requirement (or group of closely related requirements), describe the rough implementation approach in plain, human-readable language. This is NOT pseudocode — it should be understandable by both developers and product managers.

```
📐 需求：[需求摘要]
实现思路：
  用 2–4 句话描述如何实现。包括：
  - 数据流转：从哪来、存到哪、怎么取
  - 关键技术决策：用什么方案、为什么这样选
  - 与现有系统的关系：复用哪些现有模块，新增哪些
```

Example:
```
📐 需求：用户可按时间区间筛选订单
实现思路：
  前端提供预设时间选项（1h/24h/7d/自定义），选择后转换为 start_time 和 end_time（ISO 8601）传给后端。
  后端在订单查询接口增加 start_time/end_time 可选参数，使用已有 orders.created_at 索引进行范围查询。
  复用现有分页逻辑，无需新增数据表或索引。
```

Write one `📐` block per requirement or per logically grouped set of requirements. The purpose is to give the reader a quick mental model of "how this will be built" before diving into the detailed task breakdown in Step 6.

---

## Step 5: Requirements Evaluation

Systematically evaluate each requirement against four dimensions. **Only evaluate within the selected scope(s).**

For each issue found, provide:
- The specific requirement it relates to
- What the problem is
- Whether it affects frontend, backend, or both
- A concrete suggestion to fix it

### 5.1 Gap Analysis (遗漏点)

Identify requirements that are **missing but should exist**, based on:
- Common sense for this type of feature
- What the codebase implies (e.g., auth required but not mentioned, migration needed but not listed)
- Edge cases and boundary conditions not covered
- Error handling scenarios not described
- Backward compatibility concerns

### 5.2 Unreasonable Items (不合理项)

Identify requirements that are:
- Technically infeasible with the current stack
- Contradicting existing system behavior
- Disproportionately expensive relative to business value
- Conflicting with each other
- Over-specified (dictating implementation rather than outcome)
- **Mixing frontend/backend responsibilities** (e.g., requiring backend to format display text)

### 5.3 Ambiguity / Vagueness (歧义/模糊项)

Identify requirements that:
- Have multiple possible interpretations
- Lack measurable acceptance criteria
- Use subjective language ("fast", "user-friendly") without quantification
- Don't specify boundary conditions (max input size, concurrent users, etc.)

### 5.4 Risk Items (风险项)

Identify:
- Security risks (input validation, auth, data exposure)
- Performance risks (N+1 queries, unbounded lists, missing pagination)
- Data integrity risks (race conditions, missing transactions)
- Third-party dependency risks
- Migration / rollback risks

Output format for each category:

```
### 5.X [类别名]

| # | 相关需求 | 影响范围 | 问题描述 | 严重程度 | 建议 |
|---|---------|---------|---------|---------|------|
| 1 | FR-xx   | 后端    | ...     | 高/中/低 | ... |
```

If a category has no issues, explicitly state: `✅ 未发现问题`

---

## Step 6: Development Document

Produce a structured implementation plan. **Only include tasks for the selected scope(s).**

### 6.1 Architecture Impact Analysis

Describe what changes this feature requires at the architecture level (for selected scopes only):
- New modules / services / components to create
- Existing modules to modify
- Database schema changes (new tables, altered columns, new indexes)
- API changes (new endpoints, modified endpoints)
- Configuration changes

### 6.2 Task Breakdown

Break down into atomic, implementable tasks. Each task:

```
📌 Task X.Y: [任务名称]
  范围：[后端 / 前端 / 数据库 / API / 配置 / 测试]
  描述：具体做什么（2–3 句话）
  涉及文件：列出需要新建或修改的文件路径（基于 Step 3 的项目扫描结果）
  依赖：[依赖哪些其他 Task，或"无"]
  验收标准：如何验证这个 Task 完成了
```

Task naming: `X.Y` where X = feature module number, Y = sequential task number.

**Scope filtering**: If user only selected backend, do NOT create frontend tasks. Instead, for requirements that touch frontend, add a note:
```
ℹ️ 前端相关：此需求的前端部分（XXX）未纳入本次评审范围。
```

### 6.3 Database Changes (if applicable, backend scope)

- New tables: schema definition
- Altered tables: column changes
- New indexes
- Migration strategy (up and down)
- Data backfill requirements

### 6.4 API Changes (if applicable)

For each new or modified endpoint:
```
[METHOD] /api/path
  描述：做什么
  请求参数：{ field: type, ... }
  响应格式：{ field: type, ... }
  鉴权：[是否需要 / 权限级别]
  错误码：[列出可能的错误码及含义]
```

**API design must follow engineering conventions:**
- Time fields: use ISO 8601 timestamp or Unix timestamp, never relative strings
- Pagination: include `page`, `page_size` (with default and max cap), response includes `total`
- List endpoints: always have a reasonable default limit
- Error responses: consistent format with error code + message
- Sensitive fields: never expose in API response (password hash, internal IDs if applicable)

### 6.5 Testing Strategy (if testing scope selected)

- Unit tests: which modules, what scenarios
- Integration tests: which flows
- E2E tests: which user journeys (if applicable)
- Edge cases to specifically test

---

## Step 7: Effort Estimation (PERT Method)

Use **PERT Three-Point Estimation** for scientific accuracy. **Only estimate for selected scopes.**

### Methodology

For each task from Step 6.2, estimate three values:
- **O** (Optimistic): everything goes smoothly, no surprises
- **M** (Most Likely): normal development speed, minor issues
- **P** (Pessimistic): significant issues encountered, rework needed

Calculate:
- **Expected (E)** = (O + 4M + P) / 6
- **Standard Deviation (σ)** = (P − O) / 6

### Complexity Classification

| Level | Label | Typical Range | Criteria |
|-------|-------|---------------|----------|
| S | 简单 | 0.5–2h | Single file, follows existing pattern exactly, no new logic |
| M | 中等 | 2–8h | 2–5 files, follows existing patterns with minor adaptation |
| L | 复杂 | 8–24h | New patterns, cross-module changes, significant new logic |
| XL | 极复杂 | 24–40h | Architectural changes, cross-system integration, new infrastructure |

### Output Table

```
### 工时评估明细

| Task | 任务名称 | 范围 | 复杂度 | O(h) | M(h) | P(h) | E(h) | σ(h) |
|------|---------|------|--------|------|------|------|------|------|
| 1.1  | ...     | 后端 | M      | 2    | 4    | 8    | 4.3  | 1.0  |
| ...  | ...     | ...  | ...    | ...  | ...  | ...  | ...  | ...  |
```

### Category Summary

Only show categories within the selected scope(s):

```
### 工时汇总

| 类别 | 预估工时(h) | 人天(8h/天) |
|------|------------|------------|
| 后端开发 | XX.X | X.X |
| 数据库   | XX.X | X.X |
| 单元测试 | XX.X | X.X |
| Code Review | XX.X | X.X |
| **小计** | **XX.X** | **X.X** |
```

### Risk Buffer

| Risk Level | Multiplier | Trigger Conditions |
|------------|------------|-------------------|
| Low | ×1.1 (+10%) | Requirements are clear, tech stack is familiar, no external dependencies |
| Medium | ×1.25 (+25%) | Some ambiguity, moderate complexity, some new patterns |
| High | ×1.5 (+50%) | Significant ambiguity, unfamiliar tech, external dependencies, tight coupling |

```
### 风险系数

风险等级：[低 / 中 / 高]
风险系数：×X.XX
理由：[具体说明]

| 项目 | 工时 |
|------|------|
| 基础工时 | XX.X h |
| 风险缓冲 | +XX.X h |
| **最终预估** | **XX.X h（约 X.X 人天）** |
```

### Estimation Confidence

```
📊 评估置信度：[高 / 中 / 低]
评审范围：[后端 / 前端 / 测试]（仅对此范围的工时负责）
高 = 需求清晰 + 技术栈熟悉 + 同类功能有先例
中 = 部分需求待确认 + 有新技术引入
低 = 大量需求模糊 + 技术探索性强
```

---

## Step 8: Summary & Recommendations

```
## 总结

### 评审范围
[后端 / 前端 / 测试]

### 需求健康度评分
| 维度 | 评分(1-5) | 说明 |
|------|----------|------|
| 完整性 | X | ... |
| 合理性 | X | ... |
| 清晰度 | X | ... |
| 可测试性 | X | ... |
| 技术可行性 | X | ... |
| **综合** | **X.X** | ... |

### 关键建议
1. [最重要的建议]
2. ...
3. ...

### 建议优先级排序
[如果需求可以分期，建议哪些先做、哪些后做]

### 待确认事项（非阻塞）

List non-blocking ambiguities identified in Step 3.4 (Tier 2). These do not affect the current design or estimates, but should be confirmed with the product team before development starts.

```
以下需求点存在模糊之处，但不影响当前设计和工时评估。建议开发前与产品确认：

| # | 相关需求 | 模糊点 | 当前假设 |
|---|---------|--------|---------|
| 1 | [需求X] | [具体模糊描述] | [评审中采用的默认假设] |
| ...| ... | ... | ... |
```

If no non-blocking ambiguities were found, state: `✅ 无待确认事项`
```

---

## Step 9: Export (Markdown, automatic)

After all analysis is complete, **automatically** save the full document as Markdown.

**File naming**: `{feature-name}-dev-review.md`
**Save location**: project's `docs/` directory if it exists, otherwise current working directory.

The exported `.md` file must contain all sections as clean Markdown with proper headings, tables, and formatting.

After saving, output: `✅ 已保存至 {filepath}`

---

## Step 10: Follow-up

```
💬 可以继续追问：
- 「Task X.Y 的实现细节」← 展开某个具体任务
- 「需求X的遗漏点怎么补充」← 补充建议
- 「工时评估的依据是什么」← 解释评估逻辑
- 「如果砍掉需求X，工时怎么变」← 需求裁剪推演
- 「增加前端评审」← 补充扫描前端项目
- 「这个方案有什么替代方案」← 架构替代讨论
```

---

## Quality Rules

- **Codebase-grounded**: Every technical assessment must reference actual files/patterns found in Step 3. No generic advice.
- **No fabrication**: If you cannot determine something from the codebase, say so explicitly.
- **Scope-aware**: Only produce tasks and estimates for the user-selected scope(s). Do not mix in out-of-scope work.
- **Responsibility separation**: Never count pure frontend interaction work in backend estimates, and vice versa. The Requirement Responsibility Matrix (Step 4) is the single source of truth for scope assignment.
- **Engineering conventions over product language**: Always translate product descriptions into proper developer specifications. Backend stores absolute values, validates independently, and never trusts frontend input.
- **Actionable issues only**: Don't flag nitpicks. Every item must have a concrete suggestion.
- **Honest estimation**: Do not pad or underestimate. Use PERT formula strictly.
- **Maintain structure**: Follow all steps in order. Do not skip or merge steps.
- **Language**: All output in Chinese. Technical terms (API names, file paths, framework names) keep original English.

---

*The test: a developer receiving this document should be able to start implementation immediately without needing to ask "what exactly should I build?" or "how long will this take?" — and should never find a frontend task mixed into their backend estimate.*
