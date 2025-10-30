# alin-dev-cc-workflow

Claude Code 客户端专用的 alin-dev 工作流版本。

安装映射：
- `commands/*.md` → `<TARGET>/.claude/commands/`
- `agents/*.md` → `<TARGET>/.claude/agents/`

使用：
```bash
make alin-dev-to-cc TARGET=/绝对路径/你的项目
# 或者
make install-workflow WORKFLOW=alin-dev ENV=cc TARGET=/绝对路径/你的项目
```

输出文件：见 `commands/alin-dev.md` 与项目根 `docs/alin-dev-envs.md`。
