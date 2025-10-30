# alin-dev-workflow 使用说明

本目录为中性（环境无关）工作流目录，包含：

- commands：主命令文件（md）
- agents：子代理文件（md）

安装目标与映射：

- cc 环境：复制到 `<TARGET>/.claude/commands` 与 `<TARGET>/.claude/agents`
- droid 环境：复制到 `<TARGET>/.factory/commands` 与 `<TARGET>/.factory/droids`

使用 Makefile 一键安装（推荐）：

```bash
# 安装到 Claude Code（cc）
make alin-dev-to-cc TARGET=/绝对路径/你的项目

# 安装到 Droid（factory）
make alin-dev-to-droid TARGET=/绝对路径/你的项目

# 或者显式指定
make install-workflow WORKFLOW=alin-dev ENV=cc TARGET=/绝对路径/你的项目
make install-workflow WORKFLOW=alin-dev ENV=droid TARGET=/绝对路径/你的项目
```

目录命名策略：

- Makefile 将优先寻找 `<WORKFLOW>-<ENV>-workflow`（如 `alin-dev-cc-workflow`、`alin-dev-droid-workflow`）。
- 如不存在，则回退使用本目录 `alin-dev-workflow`。

因此你可以继续使用统一的 `alin-dev-workflow`，也可以在未来根据需要拆分为 `alin-dev-cc-workflow` 与 `alin-dev-droid-workflow`，无需修改 Makefile。

更多说明见：`docs/alin-dev-envs.md`。
