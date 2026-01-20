# /update-my-claude - MyClaude 自动更新命令

当用户执行 `/update-my-claude` 时，自动执行 MyClaude 仓库和组件的完整更新流程。

## 执行流程

按以下步骤顺序执行，每步完成后报告状态：

### 1. 检查当前状态
```bash
cd D:\mine\m_project\myclaude
git fetch upstream
git status
```

输出当前分支状态和是否有新的上游提交。

### 2. 显示可用更新
```bash
git log HEAD..upstream/master --oneline
```

如果没有新提交，告知用户已是最新版本并退出。

### 3. 合并上游更新
```bash
git merge upstream/master
```

如果出现冲突：
- 对于 `.claude-plugin/marketplace.json`，使用上游版本：
  ```bash
  git checkout --theirs .claude-plugin/marketplace.json
  git add .claude-plugin/marketplace.json
  ```
- 完成合并：
  ```bash
  git commit -m "Merge upstream/master: auto-update via /update-my-claude"
  ```

### 4. 更新 codeagent-wrapper
```bash
# 检查当前版本
codeagent-wrapper --version

# 下载最新版本
curl -L -o "C:\Users\Lenovo\bin\codeagent-wrapper.exe" \
  "https://github.com/cexll/myclaude/releases/latest/download/codeagent-wrapper-windows-amd64.exe"

# 验证新版本
codeagent-wrapper --version
```

报告版本变化（如：5.6.4 → 5.6.5）。

### 5. 更新技能文件
```bash
# 更新 omo 技能
cp -r D:\mine\m_project\myclaude\skills\omo/* ~/.claude/skills/omo/

# 更新 codeagent 技能
cp -r D:\mine\m_project\myclaude\skills\codeagent/* ~/.claude/skills/codeagent/

# 更新 CLAUDE.md（如果有变化）
cp D:\mine\m_project\myclaude\memorys\CLAUDE.md ~/.claude/CLAUDE.md
```

### 6. 验证更新
```bash
# 测试 codeagent-wrapper
codeagent-wrapper --help

# 创建临时测试目录
mkdir -p ~/test_update && cd ~/test_update
echo "print('test')" > test.py

# 测试基本功能
codeagent-wrapper --backend codex "Read test.py" .

# 清理
cd ~ && rm -rf ~/test_update
```

### 7. 生成更新报告

输出格式：
```
✅ MyClaude 更新完成

更新内容：
- 合并了 X 个新提交
- codeagent-wrapper: 旧版本 → 新版本
- 更新的技能: omo, codeagent

主要变更：
[列出最近 5 个提交的标题]

测试结果：
✅ codeagent-wrapper 工作正常
✅ 基本功能测试通过

配置文件位置：
- 仓库: D:\mine\m_project\myclaude
- 配置: ~/.claude/
- 文档: D:\ai-tool\myclaude\README.md
```

## 错误处理

- 如果 git merge 失败且无法自动解决，提示用户手动处理
- 如果 codeagent-wrapper 下载失败，保留旧版本并警告
- 如果测试失败，报告具体错误但不回滚

## 注意事项

- 此命令会自动提交合并，无需用户确认
- 建议在执行前确保没有未提交的重要更改
- 更新过程约需 1-2 分钟
- 如需查看详细文档，参考 `D:\ai-tool\myclaude\README.md`
