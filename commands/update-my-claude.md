# /update-my-claude - MyClaude 自动更新命令

当用户执行 `/update-my-claude` 时，自动执行 MyClaude 仓库和组件的完整更新流程。

## 使用方式

```bash
/update-my-claude              # 执行完整更新流程
/update-my-claude status       # 查看当前模型版本
/update-my-claude switch <版本> # 切换模型版本 (claude | minimax)
```

## 分支策略

- `master`: 保持与 upstream/master 完全同步（只做 fast-forward）
- `alin-dev`: 所有本地定制内容（工作分支）
- 已启用 `git rerere`，重复冲突自动解决

## 执行流程

按以下步骤顺序执行，每步完成后报告状态：

### 1. 检查参数

```bash
# 解析参数
ARG=$1  # status | switch | (空)
VERSION=$2  # claude | minimax
```

### 2. 处理 status 命令
```bash
if [ "$ARG" = "status" ]; then
  CURRENT=$(cat E:\mine\m_projects\myclaude\config\models\current.txt)
  echo "当前模型版本: $CURRENT"
  echo ""
  echo "可用版本:"
  ls E:\mine\m_projects\myclaude\config\models\*.json | xargs -I{} basename {} .json | grep -v current
  exit 0
fi
```

### 3. 处理 switch 命令
```bash
if [ "$ARG" = "switch" ]; then
  TARGET_VERSION=$2
  if [ -z "$TARGET_VERSION" ]; then
    echo "错误: 请指定版本 (claude | minimax)"
    exit 1
  fi

  if [ ! -f "E:\mine\m_projects\myclaude\config\models\$TARGET_VERSION.json" ]; then
    echo "错误: 版本 '$TARGET_VERSION' 不存在"
    echo "可用版本: claude, minimax"
    exit 1
  fi

  # 更新 current.txt
  echo "$TARGET_VERSION" > E:\mine\m_projects\myclaude\config\models\current.txt

  # 安装对应版本的 models.json
  cp E:\mine\m_projects\myclaude\config\models\$TARGET_VERSION.json ~/.codeagent/models.json

  echo "✅ 已切换到 $TARGET_VERSION 版本"
  echo ""
  echo "配置详情:"
  cat ~/.codeagent/models.json | grep -E '"default_backend"|"default_model"' | head -2

  # 如果切换到 minimax，检查环境变量
  if [ "$TARGET_VERSION" = "minimax" ]; then
    if [ -z "$CLAUDE_CODE_GIT_BASH_PATH" ]; then
      echo ""
      echo "⚠️  提示: claude backend 需要设置 CLAUDE_CODE_GIT_BASH_PATH"
      echo '   执行: export CLAUDE_CODE_GIT_BASH_PATH="E:\package\Git\Git\usr\bin\bash.exe"'
    fi
  fi

  exit 0
fi
```

### 4. 执行完整更新（默认）

#### 4.1 检查当前状态
```bash
cd E:\mine\m_projects\myclaude
git fetch upstream
git status
```

确认当前在 `alin-dev` 分支。

#### 4.2 同步 master（永远不会冲突）
```bash
git checkout master
git merge upstream/master
```

如果 master 没有新提交，告知用户已是最新版本。

#### 4.3 将上游更新合并到 alin-dev
```bash
git checkout alin-dev
git merge master
```

如果出现冲突：
- 对于上游源码文件，优先使用上游版本
- 对于本地定制文件，保留本地版本

#### 4.4 更新 codeagent-wrapper
```bash
codeagent-wrapper --version
curl -L -o "C:\Users\Administrator\bin\codeagent-wrapper.exe" \
  "https://github.com/cexll/myclaude/releases/latest/download/codeagent-wrapper-windows-amd64.exe"
codeagent-wrapper --version
```

#### 4.5 更新技能文件
```bash
git checkout alin-dev
cp -r E:\mine\m_projects\myclaude\skills\omo\* ~/.claude/skills/omo/
cp -r E:\mine\m_projects\myclaude\skills\codeagent\* ~/.claude/skills/codeagent/
cp -r E:\mine\m_projects\myclaude\skills\rrcc-course\ ~/.claude/skills/rrcc-course/
cp E:\mine\m_projects\myclaude\memorys\CLAUDE.md ~/.claude/CLAUDE.md
```

#### 4.6 安装当前模型配置
```bash
CURRENT_MODEL=$(cat E:\mine\m_projects\myclaude\config\models\current.txt)
cp E:\mine\m_projects\myclaude\config\models\$CURRENT_MODEL.json ~/.codeagent/models.json
echo "已安装 $CURRENT_MODEL 版本模型配置"
```

#### 4.7 推送 alin-dev
```bash
git push origin alin-dev
```

### 5. 生成更新报告

```
✅ MyClaude 更新完成

分支状态：
- master: 与 upstream/master 同步 ✅
- alin-dev: 已合并最新 master ✅

更新内容：
- 合并了 X 个上游新提交
- codeagent-wrapper: 旧版本 → 新版本
- 更新的技能: omo, codeagent, rrcc-course
- 模型配置: [当前版本]

主要上游变更：
[列出最近 5 个提交的标题]

测试结果：
✅ codeagent-wrapper 工作正常

配置文件位置：
- 仓库: E:\mine\m_projects\myclaude
- 工作分支: alin-dev
- 配置: ~/.claude/
- 模型配置: E:\mine\m_projects\myclaude\config\models/
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
- 模型配置存储在 `config/models/`，通过 `current.txt` 记录当前版本
