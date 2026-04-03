---
name: fse-suspend
description: Mark the current FSE requirement session as suspended and reset the workspace to WORKSPACE_READY, so the user can switch to another requirement via the session picker. The session snapshot is already auto-saved on every state transition — no manual export needed.
---

# FSE-Suspend — 暂停当前需求，切换到其他需求

将当前会话标记为 `suspended`，重置工作区到就绪状态。无需手动导出——快照已在每次状态变更时自动保存。

## Language Requirement

**All user-facing output MUST be in Chinese (Simplified).**

## Hard Constraints

1. Workspace must exist. If `.fullstack/workspace.json` not found → BLOCK.
2. If state is already `WORKSPACE_READY` → nothing to suspend, warn and exit.
3. All user-facing questions MUST use `AskUserQuestion` tool.

---

## Step 1 — Verify workspace

```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" status
python "$HOME/.claude/skills/fse/scripts/workspace.py" get-state
```

If NOT_FOUND → `BLOCKED: 未找到 FSE 工作区。`

If state is `WORKSPACE_READY` → output `当前没有正在进行的需求，无需暂停。` and stop.

---

## Step 2 — Confirm suspension

Use `AskUserQuestion`:

```
确认暂停「<feature_name_or_state_label>」？
当前阶段：<PHASE_LABEL>  |  模式：<mode>
快照已自动保存，随时可通过 /fse 恢复。
```

Options:
- `确认暂停，去做其他需求`
- `取消`

If cancelled → stop.

---

## Step 3 — Mark session as suspended

Read the current feature_id from workspace:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" get-mode
```

Update the auto-saved session's status to `suspended`:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" session-update-status \
  --session-id <feature_id> \
  --status suspended
```

Reset workspace to ready state:
```bash
python "$HOME/.claude/skills/fse/scripts/workspace.py" set-state WORKSPACE_READY
```

---

## Step 4 — Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏸ 需求已暂停
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
快照已保存至 .fullstack/sessions/<feature_id>/
包含：需求文档 · API 合约 · 分析产物 · 工作区状态

运行 /fse 可查看所有会话并继续任意需求。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<promise>FSE_SUSPENDED</promise>
```
