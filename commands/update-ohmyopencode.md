# /update-ohmyopencode - Oh My OpenCode 自动升级命令

当用户执行 `/update-ohmyopencode` 时，自动升级 oh-my-opencode 到指定版本。

## 执行流程

### 1. 检查当前状态
```bash
# 显示当前版本
oh-my-opencode --version
npm list -g oh-my-opencode
```

输出当前安装的版本信息。

### 2. 备份配置
```bash
# 备份 opencode 配置
if [ -d ~/.opencode ]; then
  cp -r ~/.opencode ~/.opencode.backup.$(date +%Y%m%d_%H%M%S)
  echo "✅ 配置已备份到 ~/.opencode.backup.$(date +%Y%m%d_%H%M%S)"
fi

# 记录当前版本
oh-my-opencode --version > ~/ohmyopencode-version-backup.txt
```

### 3. 升级到目标版本
```bash
# 升级到最新稳定版 (推荐)
npm install -g oh-my-opencode@latest

# 注意: 3.0.0-beta.8 存在平台兼容性问题，暂不推荐
# 如果用户明确要求 beta 版本，警告并询问确认
```

如果升级失败，尝试：
```bash
# 清理缓存后重试
npm cache clean --force
npm install -g oh-my-opencode@3.0.0-beta.8 --force
```

### 4. 验证升级
```bash
# 检查新版本
oh-my-opencode --version
npm list -g oh-my-opencode

# 验证 opencode 仍然正常
opencode --version
```

### 5. 测试功能
```bash
# 检查配置是否正常
oh-my-opencode config list

# 测试基本命令
oh-my-opencode --help
```

### 6. 生成升级报告

输出格式：
```
✅ Oh My OpenCode 升级完成

版本变更：
- 旧版本: 2.13.2
- 新版本: 2.14.0 (最新稳定版)

备份信息：
- 配置备份: ~/.opencode.backup.20260116_105000 (如有)
- 版本记录: ~/ohmyopencode-version-backup.txt

验证结果：
✅ oh-my-opencode 命令正常
✅ opencode 命令正常
✅ 配置文件完整

注意事项：
ℹ️  已升级到最新稳定版 2.14.0
⚠️  3.0.0-beta.8 存在平台兼容性问题，暂不推荐升级
ℹ️  等待 3.0 正式版发布后再升级

配置文件位置：
- OpenCode 配置: ~/.opencode/
- 文档: D:\ai-tool\myclaude\ohmyopencode\README.md
```

## 错误处理

### 升级失败
- 清理 npm 缓存并重试
- 如仍失败，提示用户检查网络连接
- 保留旧版本，不强制升级

### 配置损坏
- 从备份恢复配置
- 提示用户手动检查配置

### 版本验证失败
- 显示实际安装的版本
- 提示可能需要重启终端

## 可选参数

### 升级到其他版本
用户可以指定版本：
```bash
/update-ohmyopencode 2.14.0
/update-ohmyopencode latest
```

如果没有指定版本，默认升级到 `latest` (最新稳定版)。

**不推荐**: 由于平台兼容性问题，暂不支持升级到 beta 版本。

## 回滚命令

如果升级后出现问题，提供快速回滚：
```bash
# 回滚到备份的版本
npm install -g oh-my-opencode@$(cat ~/ohmyopencode-version-backup.txt)

# 恢复配置
cp -r ~/.opencode.backup.* ~/.opencode
```

## 注意事项

- 升级过程需要网络连接
- 可能需要管理员权限（Windows）
- 升级时间约 30 秒 - 1 分钟
- Beta 版本可能不稳定，建议在非生产环境测试
