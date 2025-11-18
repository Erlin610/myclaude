# alin-dev-cc-workflow

Claude Code 客户端专用的 alin-dev 工作流版本。

## 前置条件

### Codex CLI（推荐，用于复杂任务）
- 安装 Codex CLI：https://docs.codex.anthropic.com/install
- 确保 `codex` 命令在 PATH 中可用
- Python 3.8+ （用于 skill wrapper）

如果未安装 Codex CLI，工作流会自动降级到 Claude Code 原生实现。

## 安装

安装映射：
- `commands/*.md` → `<TARGET>/.claude/commands/`
- `agents/*.md` → `<TARGET>/.claude/agents/`

使用：
```bash
make alin-dev-to-cc TARGET=/绝对路径/你的项目
# 或者
make install-workflow WORKFLOW=alin-dev ENV=cc TARGET=/绝对路径/你的项目
```

## 工作流说明

- **Codex-First 策略**：逻辑改动默认使用 Codex Skill（通过 `~/.claude/skills/codex/scripts/codex.py`）
- **自动降级**：Codex CLI 不可用时自动使用 Claude Code 原生实现
- **强制路由**：使用 `--force-cc` 或 `--force-codex` 覆盖自动路由决策

输出文件：见 `commands/alin-dev.md` 与项目根 `docs/alin-dev-envs.md`。
