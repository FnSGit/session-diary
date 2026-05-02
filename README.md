# Session Diary Plugin

Lightweight session diary hooks for Claude Code - zero dependencies, zero vector DB.

## Why This Exists

**问题：** MemPalace 占用大量资源（Qdrant vector DB + GPU），WSL GPU 虚拟化导致崩溃断联。

**解决方案：** 提取 session diary 功能独立为轻量级包，仅保留 hooks + markdown storage，移除所有重型依赖。

## Features

- ✅ **零依赖**：仅使用 Python 标准库（无第三方包）
- ✅ **零资源占用**：无 vector DB、无 GPU、无后台进程
- ✅ **快速安装**：`uv tool install session-diary-plugin`
- ✅ **自动配置**：`session-diary-install` 一键配置 hooks
- ✅ **向后兼容**：自动读取新旧格式 diary
- ✅ **增量摘要**：30KB 大小控制，自动裁剪旧条目

## Installation

```bash
# 1. Install via uv tool
uv tool install session-diary-plugin

# 2. Verify installation
uv tool list

# 3. Configure Claude Code
session-diary-install

# 4. Restart Claude Code
```

## Configuration

Environment variables:
- `SESSION_DIARY_SAVE_INTERVAL=15` (default: 15 messages)
- `SESSION_DIARY_VERBOSE=false` (default: silent mode)
- `SESSION_DIARY_MEMORY_DIR=.session-memory` (default: .session-memory)

## License

MIT
