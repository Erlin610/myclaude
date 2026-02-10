# /update-my-claude - MyClaude 自动更新命令

当用户执行 `/update-my-claude` 时，自动执行 MyClaude 仓库和组件的完整更新流程。

## 分支策略

- `master`: 保持与 upstream/master 完全同步（只做 fast-forward）
- `alin-dev`: 所有本地定制内容（工作分支）
- 已启用 `git rerere`，重复冲突自动解决

## 执行流程

按以下步骤顺序执行，每步完成后报告状态：

### 1. 检查当前状态
```bash
cd E:\mine\m_projects\myclaude
git fetch upstream
git status
```

确认当前在 `alin-dev` 分支。如果不在，先切换：`git checkout alin-dev`

### 2. 同步 master（永远不会冲突）
```bash
git checkout master
git merge upstream/master
```

这一步永远是 fast-forward，不会有冲突。

如果 master 没有新提交（`git log HEAD..upstream/master --oneline` 为空），告知用户已是最新版本并退出。

### 3. 将上游更新合并到 alin-dev
```bash
git checkout alin-dev
git merge master
```

如果出现冲突：
- 对于上游源码文件（`codeagent-wrapper/`, `skills/do/`, `memorys/`），优先使用上游版本：
  ```bash
  git checkout --theirs <conflicted-file>
  git add <conflicted-file>
  ```
- 对于 `config.json`，手动合并：保留本地新增模块 + 上游新增模块
- 对于本地定制文件（`skills/rrcc-course/`, `skills/think-tank/` 等），保留本地版本：
  ```bash
  git checkout --ours <conflicted-file>
  git add <conflicted-file>
  ```
- 完成合并：
  ```bash
  git commit -m "Merge master into alin-dev: auto-update via /update-my-claude"
  ```

### 4. 更新 codeagent-wrapper
```bash
# 检查当前版本
codeagent-wrapper --version

# 下载最新版本
curl -L -o "C:\Users\Administrator\bin\codeagent-wrapper.exe" \
  "https://github.com/cexll/myclaude/releases/latest/download/codeagent-wrapper-windows-amd64.exe"

# 验证新版本
codeagent-wrapper --version
```

报告版本变化（如：v6.5.1 → v6.6.0）。

### 5. 更新技能文件（从 alin-dev 分支安装）
```bash
# 确保在 alin-dev 分支
git checkout alin-dev

# 更新 omo 技能
cp -r E:\mine\m_projects\myclaude\skills\omo\* ~/.claude/skills/omo/

# 更新 codeagent 技能
cp -r E:\mine\m_projects\myclaude\skills\codeagent\* ~/.claude/skills/codeagent/

# 更新 rrcc-course 技能
cp -r E:\mine\m_projects\myclaude\skills\rrcc-course\ ~/.claude/skills/rrcc-course/

# 更新 CLAUDE.md（如果有变化）
cp E:\mine\m_projects\myclaude\memorys\CLAUDE.md ~/.claude/CLAUDE.md
```

### 6. 推送 alin-dev
```bash
git push origin alin-dev
```

### 7. 生成更新报告

输出格式：
```
✅ MyClaude 更新完成

分支状态：
- master: 与 upstream/master 同步 ✅
- alin-dev: 已合并最新 master ✅

更新内容：
- 合并了 X 个上游新提交
- codeagent-wrapper: 旧版本 → 新版本
- 更新的技能: omo, codeagent, rrcc-course

主要上游变更：
[列出最近 5 个提交的标题]

测试结果：
✅ codeagent-wrapper 工作正常

配置文件位置：
- 仓库: E:\mine\m_projects\myclaude
- 工作分支: alin-dev
- 配置: ~/.claude/
```

## 错误处理

- master 同步永远不应失败（pure fast-forward）
- 如果 alin-dev merge 失败且 rerere 无法自动解决，提示用户手动处理
- 如果 codeagent-wrapper 下载失败，保留旧版本并警告
- 如果测试失败，报告具体错误但不回滚

## 注意事项

- 此命令会自动提交合并，无需用户确认
- 建议在执行前确保 alin-dev 没有未提交的重要更改
- 更新过程约需 1-2 分钟
- 工作分支始终是 `alin-dev`，不要在 `master` 上做任何本地修改
