#!/usr/bin/env bash
# fse-test 独立安装脚本
# 用法: bash install.sh
set -e

SKILL_DIR="$HOME/.claude/skills/fse-test"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== fse-test 安装 ==="
echo "安装目录: $SKILL_DIR"

# 1. 创建目录
mkdir -p "$SKILL_DIR/scripts"

# 2. 复制文件
cp "$SCRIPT_DIR/SKILL.md" "$SKILL_DIR/SKILL.md"
cp "$SCRIPT_DIR/scripts/workspace.py" "$SKILL_DIR/scripts/workspace.py"

echo "✓ SKILL.md 已安装"
echo "✓ workspace.py 已安装"

# 3. 检查依赖
echo ""
echo "=== 依赖检查 ==="

# Python
if command -v python3 &>/dev/null; then
  echo "✓ Python: $(python3 --version)"
elif command -v python &>/dev/null; then
  echo "✓ Python: $(python --version)"
else
  echo "✗ Python 未安装 — 请安装 Python 3.8+"
fi

# Node / npm
if command -v npm &>/dev/null; then
  echo "✓ npm: $(npm --version)"
else
  echo "✗ npm 未安装 — 请安装 Node.js 18+ (https://nodejs.org)"
fi

# codeagent-wrapper
if command -v codeagent-wrapper &>/dev/null; then
  echo "✓ codeagent-wrapper: $(codeagent-wrapper --version 2>/dev/null || echo '已安装')"
else
  echo "✗ codeagent-wrapper 未安装"
  echo "  → 请联系技能提供者获取安装方式"
fi

# Claude Code
if command -v claude &>/dev/null; then
  echo "✓ Claude Code: 已安装"
else
  echo "✗ Claude Code 未安装 — https://claude.ai/code"
fi

echo ""
echo "=== 安装完成 ==="
echo "在 Claude Code 中执行 /fse-test 即可使用"
echo ""
echo "可选：安装 Playwright MCP（用于失败截图调查）"
echo "  claude mcp add playwright"
