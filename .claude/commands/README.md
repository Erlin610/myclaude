# 项目初始化工具

## init-project-command

这是一个强大的项目初始化命令，用于自动分析项目文档并生成完整的 Claude Code 工作流配置。

### 功能特性

- **智能文档分析**: 自动读取项目目录下的所有文档（.md, .txt, .pdf），提取项目信息
- **用户确认机制**: 通过交互式问题确认提取的信息
- **完整配置生成**: 自动生成项目特定的配置文件和命令

### 生成内容

运行 `/init-project-command <项目目录>` 后，会在目标项目中创建：

```
<项目目录>/.claude/
├── project.yaml              # 项目配置（用户画像、技术栈、UX约束）
├── CLAUDE.md                # 项目AI协作指令
├── commands/
│   ├── pm.md               # 产品经理模式
│   ├── ux.md               # UI/UX设计师模式
│   ├── dev.md              # 开发模式
│   ├── test.md             # 测试模式
│   └── workflow.md         # 工作流导航器
└── agents/
    └── dev-plan-generator.md  # 开发计划生成器
```

### 使用方法

```bash
/init-project-command ~/path/to/your/project
```

### 工作流程

1. **文档分析**: 读取目标项目的所有文档
2. **信息提取**: AI 提取项目名称、行业、用户画像、技术栈、UX约束等
3. **用户确认**: 通过 4 个问题确认提取的信息
4. **配置生成**: 生成完整的 .claude/ 目录结构
5. **依赖复制**: 自动复制 /dev 命令及其依赖的 agents

### 核心特性

- ✅ **项目特定上下文**: 所有生成的命令都引用 project.yaml
- ✅ **用户画像驱动**: PM 基于用户画像分析需求
- ✅ **约束验证**: UX 设计时强制验证所有约束
- ✅ **技术栈适配**: Dev 使用正确的技术栈
- ✅ **完整工作流**: PM → UX → Dev → Test 无缝衔接

### 示例

参考 `~/project/agi-native-os-design` 项目，这是使用此命令初始化的完整示例。

### 设计理念

基于 Linus Torvalds 的简化原则：
- 通用命令 + 项目配置文件，而非为每个项目生成完全不同的命令
- 复杂度降低 10 倍，但解决 90% 的问题
- 避免创建大量子代理，用配置文件的画像描述代替

---

更多信息请查看命令文件：`init-project-command.md`

## 升级命令

### update-my-claude

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

### update-ohmyopencode

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
