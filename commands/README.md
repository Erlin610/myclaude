# MyClaude 升级命令

本目录包含 MyClaude 项目的自动化升级命令定义。

## 可用命令

### 1. /update-my-claude
自动更新 MyClaude 仓库和组件。

**功能：**
- 从上游仓库拉取最新更新
- 自动合并更改（处理常见冲突）
- 更新 codeagent-wrapper 二进制文件
- 同步技能文件到 ~/.claude/
- 验证更新并生成报告

**使用方法：**
```bash
/update-my-claude
```

详细文档：[update-my-claude.md](./update-my-claude.md)

---

### 2. /update-ohmyopencode
自动升级 oh-my-opencode 到最新版本。

**功能：**
- 检查当前版本
- 备份配置文件
- 升级到最新稳定版
- 验证升级结果
- 生成升级报告

**使用方法：**
```bash
/update-ohmyopencode
/update-ohmyopencode 2.14.0  # 指定版本
```

详细文档：[update-ohmyopencode.md](./update-ohmyopencode.md)

---

## 安装这些命令

这些命令定义文件可以被 Claude Code 识别并执行。将它们添加到你的技能目录：

```bash
# 复制到 Claude Code 技能目录
cp commands/*.md ~/.claude/skills/
```

或者在 Claude Code 中直接引用这些文件。

## 跨设备使用

这些命令定义存储在 `alin-dev` 分支中，可以在不同设备上使用：

```bash
# 在新设备上
cd /path/to/myclaude
git checkout alin-dev
git pull origin alin-dev

# 命令定义位于 commands/ 目录
```

## 贡献

如需添加新的升级命令或改进现有命令，请：
1. 在 `commands/` 目录创建新的 `.md` 文件
2. 遵循现有命令的格式和结构
3. 提交到 `alin-dev` 分支

## 注意事项

- 这些命令假设特定的目录结构和环境配置
- 在使用前请确保路径配置正确
- Windows 和 Unix 系统的路径可能需要调整
