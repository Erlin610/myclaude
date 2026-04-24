---
name: fse-contract
description: Define the API contract (OpenAPI spec) as the shared source of truth between frontend and backend. Both sides agree on endpoints, request/response schemas, and auth before any code is written.
---

# FSE-Contract — API Contract Definition

Produces a complete OpenAPI contract from the analysis API surface. Both frontend and backend treat this as the binding interface definition. Blocks on user confirmation (GATE-3).

## Language Requirement

**All user-facing output MUST be in Chinese (Simplified).** This includes all prompts, questions, status banners, error messages, confirmation gates, and progress displays shown to the user. Internal skill instructions may remain in English.

## Hard Constraints

1. **Contract must be defined before development starts.** Frontend and backend both reference this.
2. Every endpoint identified in `fse-analysis` must appear in the contract — no gaps.
3. **User must confirm** before state advances.
4. Contract is written to `.fullstack/contracts/<FEATURE_ID>/openapi.yaml`.
5. **All user-facing questions and confirmations MUST use `AskUserQuestion` tool.** Never show text prompts expecting free-form reply.

## Step 1 — Mark state

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state CONTRACT_DEFINING
```

```bash
FEATURE_ID=$(python "$HOME/.claude/skills/fse/scripts/workspace.py" get-feature-id 2>/dev/null)
REQ_DIR=".fullstack/requirements/$FEATURE_ID"
ANALYSIS_DIR=".fullstack/analysis/$FEATURE_ID"
CONTRACTS_DIR=".fullstack/contracts/$FEATURE_ID"
mkdir -p "$CONTRACTS_DIR"
```

## Step 2 — Load inputs

Read:
- `$ANALYSIS_DIR/api-surface.md` — endpoint outline from analysis
- `$REQ_DIR/confirmed.md` — for data shape and business rules
- Backend project structure — to align with existing patterns (auth headers, error format, pagination)

Run a quick backend convention scan:

```bash
codeagent-wrapper --agent code-explorer - <backend_path> <<'EOF'
Scan the existing API layer to identify conventions:
1. Base URL path prefix (e.g. /api/v1)
2. Authentication mechanism (e.g. Bearer token in Authorization header, session cookie)
3. Standard error response format (fields: code, message, data, etc.)
4. Pagination convention (page/size or cursor-based; response wrapper structure)
5. Date/time format used in JSON (ISO 8601? timestamp?)
6. Any existing shared DTOs or response wrappers to reuse

Return as a structured list.
EOF
```

## Step 3 — Generate OpenAPI contract

```bash
codeagent-wrapper --agent code-architect - . <<'EOF'
Generate a complete OpenAPI 3.0 YAML specification for this feature.

Inputs:
- API surface: $ANALYSIS_DIR/api-surface.md
- Requirements: $REQ_DIR/confirmed.md
- Backend conventions: <output from Step 2>

Requirements for the spec:
1. openapi: "3.0.3"
2. Use $ref for reusable schemas (no inline duplication)
3. Every endpoint must have: summary, operationId, request schema, response schemas (200 + error codes)
4. Include authentication requirement on each protected endpoint
5. Use existing backend error/pagination wrappers exactly as detected
6. Include examples for each request and response
7. IDEMPOTENCY MATRIX: For each POST/PUT/DELETE endpoint, explicitly specify:
   - Is this operation idempotent? (calling it twice produces the same result?)
   - If YES: document the mechanism (unique DB constraint / conditional update / idempotency-key header)
     and add `x-idempotent: true` to the endpoint's extension fields.
   - If NO: document the frontend responsibility (disable button on submit / show loading state)
     and add `x-idempotent: false`.
   This field is mandatory on every mutation endpoint — no silent omissions.

Write the complete YAML to $CONTRACTS_DIR/openapi.yaml
EOF
```

## Step 4 — Produce human-readable contract summary

Write `$CONTRACTS_DIR/contract-summary.md` (i.e. .fullstack/contracts/<FEATURE_ID>/...):

```markdown
# API Contract Summary

Version: 1.0.0
Generated: <timestamp>
Spec: $CONTRACTS_DIR/openapi.yaml

## Endpoints

### GET /api/users
**Purpose**: Fetch paginated user list
**Auth**: Bearer token required
**Request**:
  - Query: `page` (int, default 1), `size` (int, default 20), `keyword` (string, optional)
**Response 200**:
  ```json
  {
    "code": 200,
    "data": {
      "total": 100,
      "list": [{ "id": 1, "name": "...", "email": "..." }]
    }
  }
  ```
**Error codes**: 401 Unauthorized, 403 Forbidden, 500 Server Error

---

### POST /api/users
...

## Shared Schemas
- `User`: id, name, email, createdAt, status
- `PageResult<T>`: total, list, page, size
- `ApiResponse<T>`: code, message, data
```

## Step 5 — Confirmation Gate (GATE-3)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GATE-3：API 合约确认
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
合约：$CONTRACTS_DIR/openapi.yaml (i.e. .fullstack/contracts/<FEATURE_ID>/openapi.yaml)
定义的接口：<N>
共享 Schema：<N>

[contract-summary.md content]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
此合约是前后端的约束性接口定义。此后的变更需要先更新合约。

  1. 确认 — 进入开发
  2. 修改 — 对接口或 Schema 提供反馈
```

**Use `AskUserQuestion` tool** for this confirmation.

**如果选择"确认"：**
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state CONTRACT_CONFIRMED
```
输出：`<promise>FSE_PHASE_COMPLETE</promise>`

**如果选择"修改"：** 更新规格和摘要，重新展示。
