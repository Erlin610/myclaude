# alin-dev 环境与部署规则

本项目的 `alin-dev-workflow` 可同时部署到两类环境：

- cc 环境：目标目录使用 `.claude/commands` 与 `.claude/agents`
- droid 环境：目标目录使用 `.factory/commands` 与 `.factory/droids`

规则说明：

- commands：主命令文件（md）
- agents/droids：子代理文件（md）

Makefile 已提供一键安装命令：

- 通用安装：`make install-workflow WORKFLOW=alin-dev ENV=cc TARGET=/绝对路径`
- 通用安装：`make install-workflow WORKFLOW=alin-dev ENV=droid TARGET=/绝对路径`
- 便捷别名（cc）：`make alin-dev-to-cc TARGET=/绝对路径`
- 便捷别名（droid）：`make alin-dev-to-droid TARGET=/绝对路径`

目录兼容策略：

- 优先寻找：`<WORKFLOW>-<ENV>-workflow`（例如：`alin-dev-cc-workflow`、`alin-dev-droid-workflow`）
- 若不存在，回退到：`<WORKFLOW>-workflow`（例如：`alin-dev-workflow`）

因此你可以：

1) 维持单一目录 `alin-dev-workflow`，同时服务于 cc 与 droid 两个安装目标。
2) 或者根据需要，后续拆分为 `alin-dev-cc-workflow` 与 `alin-dev-droid-workflow`，Makefile 无需变更即可适配。

示例：

```bash
# 安装到 Claude Code（cc）
make alin-dev-to-cc TARGET=/mnt/d/your_project

# 安装到 Droid（factory）
make alin-dev-to-droid TARGET=/mnt/d/your_project

# 显式方式（与上面等价）
make install-workflow WORKFLOW=alin-dev ENV=cc TARGET=/mnt/d/your_project
make install-workflow WORKFLOW=alin-dev ENV=droid TARGET=/mnt/d/your_project
```

文件落位：

- cc：
  - `commands/*.md` → `<TARGET>/.claude/commands/`
  - `agents/*.md` → `<TARGET>/.claude/agents/`
- droid：
  - `commands/*.md` → `<TARGET>/.factory/commands/`
  - `agents/*.md` → `<TARGET>/.factory/droids/`

注意事项：

- 请确保 `TARGET` 是绝对路径且存在。
- 当前仓库提供的目录为 `alin-dev-workflow`（中性目录）。若未来新增 `alin-dev-cc-workflow` 或 `alin-dev-droid-workflow`，无需修改 Makefile。
