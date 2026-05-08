# Session Diary Plugin

> Claude Code 轻量级会话日记插件 - 零依赖，零向量数据库

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-89%25-green.svg)](tests/)

[English](README.md) | **中文文档**

## 为什么开发这个插件

**问题：** MemPalace 消耗大量资源（Qdrant 向量数据库 + GPU），WSL GPU 虚拟化会导致崩溃。

**解决方案：** 将会话日记功能提取为轻量级包 - 仅 hooks + markdown 存储，无重型依赖。

## 功能特性

- ✅ **零依赖** - 纯 Python 标准库（无第三方包）
- ✅ **零资源占用** - 无向量数据库、无 GPU、无后台进程
- ✅ **快速安装** - `uv tool install session-diary-plugin`
- ✅ **自动配置** - `session-diary-install` 一键配置 hooks
- ✅ **向后兼容** - 自动读取新旧日记格式
- ✅ **增量摘要** - 30KB 大小限制，自动裁剪旧条目
- ✅ **智能节流** - 双重触发条件（消息数 + 时间间隔）
- ✅ **自定义配置** - 支持 settings.local.json 配置日记目录

## 架构

```
Claude Code Hook 机制
    ├── Stop Hook（会话结束时触发）
    │   └── 双重条件：N 条消息 + 时间间隔
    │       ├── 计数消息数
    │       ├── 提取历史摘要
    │       ├── 生成当前条目
    │       ├── 增量累积并裁剪（30KB 限制）
    │       └── 写入 Markdown 日记文件
    │
    └── SessionStart Hook（新会话开始时触发）
        └── 读取最新日记文件
            ├── 提取历史任务摘要
            ├── 提取最近进展
            └── 注入到系统提示词
```

## 安装

```bash
# 1. 使用 uv tool 安装
uv tool install session-diary-plugin

# 2. 验证安装
uv tool list
# 预期输出：
# session-diary-plugin v1.0.0
# - session-diary-install
# - session-diary-save-hook
# - session-diary-sessionstart-hook

# 3. 配置 Claude Code
session-diary-install

# 4. 重启 Claude Code
```

## 配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SESSION_DIARY_SAVE_INTERVAL` | `15` | 保存间隔（消息数） |
| `SESSION_DIARY_MIN_INTERVAL` | `30` | 最小时间间隔（分钟） |
| `SESSION_DIARY_VERBOSE` | `false` | 详细模式（显示在对话中） |
| `SESSION_DIARY_MEMORY_DIR` | `.session-memory` | 日记目录名称 |
| `SESSION_DIARY_STATE_DIR` | `~/.session-diary/hook_state` | 状态目录 |

### settings.local.json

为每个项目自定义日记目录：

```json
// .claude/settings.local.json
{
  "sessionDiary": {
    "directory": ".session-memory"
  }
}
```

或简化格式：

```json
{
  "sessionDiaryDirectory": ".session-memory"
}
```

**优先级：** 环境变量 > settings.local.json > wrapper 解码 > 默认值

### 日记文件格式

生成文件：`.session-diary-YYYY-MM-DD-HHMM-topic.md`

```markdown
# Session Diary - YYYY-MM-DD HH:MM

## 历史任务摘要

### YYYY-MM-DD HH:MM 任务标题
- **成果：** 关键成就
- **决策：** 重要决策

---

## 本次进展

### 任务标题
- 具体进展
- 代码变更摘要
- 问题解决过程

## 关键发现

- 发现 1
- 发现 2

## 关键决策

**决策 1：选择与原因**
- 原因说明
```

## 开发

### 设置开发环境

```bash
# 克隆仓库
git clone git@github.com:FnSGit/session-diary.git
cd session-diary

# 创建虚拟环境（Python 3.14）
uv venv --python 3.14
source .venv/bin/activate  # Linux/macOS

# 安装开发依赖
uv pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并查看覆盖率
pytest --cov=session_diary --cov-report=term-missing

# 覆盖率要求：>= 80%
```

### 本地测试 Hooks

```bash
# 测试 Stop Hook
echo '{"session_id":"test","stop_hook_active":false,"transcript_path":"/tmp/test.jsonl"}' | session-diary-save-hook

# 测试 SessionStart Hook
session-diary-sessionstart-hook

# 测试安装工具
session-diary-install --dry-run
```

## 模块结构

| 模块 | 职责 | 入口点 |
|------|------|--------|
| `save_hook.py` | Stop Hook 主逻辑 | `main()` |
| `sessionstart_hook.py` | SessionStart Hook 逻辑 | `main()` |
| `installer.py` | 自动配置工具 | `main()` |
| `extractor.py` | 摘要提取 | 辅助函数 |
| `config.py` | 配置与路径解析 | 常量 |
| `state.py` | Hook 状态持久化 | `HookState` 类 |
| `counter.py` | 消息计数 | `count_exchanges()` |

## 常见问题

**Q: Hook 没有触发？**
- 检查 `~/.claude/settings.json` 配置
- 确认已重启 Claude Code
- 查看日志：`~/.session-diary/hook_state/hook.log`

**Q: 日记文件在哪里？**
- 默认：项目根目录下的 `.session-memory/`
- 可通过环境变量或 settings.local.json 自定义

**Q: 如何调试？**
- 设置 `SESSION_DIARY_VERBOSE=true`
- 查看 hook.log
- 使用 pytest 运行测试

**Q: 如何自定义日记目录？**
- 在 `.claude/settings.local.json` 中添加 `sessionDiary.directory`
- 路径相对于 `.claude` 父目录解析

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 更新日志

### 2026-05-05
- 新增 settings.local.json 配置支持
- 改进 wrapper 目录名解码（递归算法）
- 测试覆盖率：84 个测试，89.47%

### 2026-05-03
- 初始发布
- 完整 hook 实现
- 自动配置安装工具
- 73 个测试，94.58% 覆盖率