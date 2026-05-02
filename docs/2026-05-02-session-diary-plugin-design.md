# Session Diary Plugin - 设计文档

**日期：** 2026-05-02
**作者：** Claude (brainstorming skill)
**状态：** Design complete, pending implementation

---

## 概述

### 问题背景

MemPalace 项目占用大量资源：
- Qdrant vector DB + GPU 加速
- WSL2 GPU 虚拟化导致崩溃断联
- 数据量超过 200k，超出 Qdrant 单机能力

### 解决方案

提取 session diary 功能独立为轻量级 Python 包：
- 移除所有重型依赖（Qdrant/vector DB/GPU）
- 保留 hooks + markdown diary 核心功能
- 零外部依赖（仅 Python 标准库）
- uv tool 安装，自动配置

### 核心价值

- ✅ **零资源占用**：无 vector DB、无 GPU、无后台进程
- ✅ **零外部依赖**：仅使用 Python 标准库
- ✅ **快速安装**：`uv tool install session-diary-plugin`
- ✅ **自动配置**：`session-diary-install` 一键配置 hooks
- ✅ **向后兼容**：自动读取新旧格式 diary
- ✅ **增量摘要**：30KB 大小控制，自动裁剪旧条目

---

## 架构设计

### 项目结构

```
session-diary-plugin/
├── session_diary/
│   ├── __init__.py            # 包元数据（version, author）
│   ├── save_hook.py           # Stop hook 主逻辑
│   ├── sessionstart_hook.py   # SessionStart hook 主逻辑
│   ├── extractor.py           # Summary extraction 函数
│   ├── counter.py             # Message counting
│   ├── state.py               # Hook state 管理
│   ├── config.py              # 配置常量
│   └── installer.py           # 自动配置助手
├── tests/
│   ├── test_extractor.py      # 测试 summary extraction
│   ├── test_counter.py        # 测试 message counting
│   ├── test_save_hook.py      # 测试 save hook
│   ├── test_sessionstart_hook.py
│   ├── test_installer.py
│   └── conftest.py            # Fixtures（diary samples）
├── docs/
│   └── 2026-05-02-session-diary-plugin-design.md  # 设计文档
├── pyproject.toml             # uv tool 安装配置
├── README.md                  # 用户文档
└── LICENSE                    # MIT
```

### 模块职责

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| `save_hook.py` | Stop hook 主入口 | stdin: JSON (session_id, transcript_path) | stdout: JSON block decision |
| `sessionstart_hook.py` | SessionStart hook 主入口 | 无 | stdout: formatted memory injection |
| `extractor.py` | Summary extraction 函数 | diary file path | summary section text |
| `counter.py` | 计数 human messages | transcript JSONL path | exchange count |
| `state.py` | 管理 hook state | session_id, count | 读写 ~/.session-diary/hook_state |
| `config.py` | 配置常量 | 无 | SAVE_INTERVAL=15, STATE_DIR, etc. |
| `installer.py` | 配置助手 | 无 | 自动修改 .claude/settings.local.json |

---

## 核心函数设计

### extractor.py - Summary Extraction

从现有 bash 函数迁移到 Python，保持逻辑一致。

**核心函数：**

```python
def extract_summary_section(diary_path: Path) -> str:
    """Extract summary section from diary file
    
    Args:
        diary_path: Path to .session-diary-*.md file
    
    Returns:
        Summary section content (from "## 历史任务摘要" to "---")
        Empty string if not found
    """
    content = diary_path.read_text()
    
    start_marker = "## 历史任务摘要"
    end_marker = "---"
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        return ""
    
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        return content[start_idx:]
    
    return content[start_idx:end_idx + len(end_marker)]


def generate_current_entry(diary_path: Path, timestamp: str) -> str:
    """Generate current session summary entry
    
    Args:
        diary_path: Path to current diary
        timestamp: "YYYY-MM-DD HH:MM" format
    
    Returns:
        Formatted entry: "### YYYY-MM-DD HH:MM Task Title\n- **成果：** ...\n- **决策：** ..."
    """
    content = diary_path.read_text()
    
    # Extract task title: first ### in "## 本次进展"
    task_title = extract_first_task_title(content)
    
    # Extract outcomes: bullets from "## 关键发现" (max 5)
    outcomes = extract_outcomes(content, max_count=5)
    
    # Extract decisions: from "## 关键决策" (max 3)
    decisions = extract_decisions(content, max_count=3)
    
    return f"### {timestamp} {task_title}\n- **成果：** {outcomes}\n- **决策：** {decisions}"


def accumulate_and_trim_summary(old_summary: str, new_entry: str) -> str:
    """Accumulate and trim summary entries (size control: 30KB)
    
    Args:
        old_summary: Full summary section content
        new_entry: New entry to prepend
    
    Returns:
        Combined summary with size control (max 30KB, trim oldest 5 entries if exceeded)
    """
    # Remove header and separator from old content
    old_content = remove_summary_metadata(old_summary)
    
    # Build new summary
    new_summary = f"## 历史任务摘要（截止本次会话）\n\n{new_entry}\n\n{old_content}\n\n---"
    
    # Check size (30KB = 30720 bytes)
    if len(new_summary.encode('utf-8')) > 30720:
        entries = extract_summary_entries(new_summary)
        
        if len(entries) > 5:
            # Keep new entry + 5 newest old entries (total 6)
            trimmed_entries = entries[:6]
            new_summary = rebuild_summary(trimmed_entries)
    
    return new_summary
```

**对比现有 bash 实现的优势：**

| 方面 | Bash | Python |
|------|------|--------|
| 文件读取 | `sed -n '/pattern/,/pattern/p'` | `Path.read_text()` + `find()` |
| 正则提取 | `grep -E 'pattern' \| sed 's/...'` | `re.findall()` 或字符串方法 |
| 字节计数 | `wc -c` | `len(text.encode('utf-8'))` |
| 错误处理 | `if [ ! -f "$path" ]; return 1` | `try-except` 或 `Path.exists()` |
| 测试难度 | source + assert output | 直接 import + pytest |

### counter.py - Message Counting

替代现有 Python 脚本片段（在 bash 中通过 `$MEMPAL_PYTHON_BIN -c` 调用）。

```python
import json
from pathlib import Path

def count_human_messages(transcript_path: Path) -> int:
    """Count human messages in JSONL transcript
    
    Args:
        transcript_path: Path to .jsonl transcript file
    
    Returns:
        Number of user messages (excluding command messages)
    """
    count = 0
    
    with transcript_path.open('r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                msg = entry.get('message', {})
                
                if isinstance(msg, dict) and msg.get('role') == 'user':
                    content = msg.get('content', '')
                    
                    # Skip command messages (e.g., <command-message>)
                    if isinstance(content, str) and '<command-message>' in content:
                        continue
                    
                    count += 1
            except json.JSONDecodeError:
                continue
    
    return count
```

### save_hook.py - Stop Hook 主逻辑

将现有 352 行 bash 脚本重构为 Python。

```python
import json
import sys
from pathlib import Path
from .counter import count_human_messages
from .extractor import extract_summary_section, generate_current_entry, accumulate_and_trim_summary
from .state import HookState
from .config import SAVE_INTERVAL, STATE_DIR, DIARY_DIR

def main():
    """Stop hook main entry point
    
    Input (stdin JSON): {"session_id": "...", "stop_hook_active": false, "transcript_path": "..."}
    Output (stdout JSON): {} or {"decision": "block", "reason": "..."}
    """
    input_data = read_stdin_json()
    
    session_id = input_data.get('session_id', 'unknown')
    stop_hook_active = input_data.get('stop_hook_active', False)
    transcript_path = Path(input_data.get('transcript_path', ''))
    
    # Infinite loop prevention
    if stop_hook_active:
        output_empty()
        return
    
    # Count exchanges
    exchange_count = count_human_messages(transcript_path)
    
    # Check if time to save
    state = HookState(session_id)
    since_last = exchange_count - state.last_save
    
    state.log(f"Session {session_id}: {exchange_count} exchanges, {since_last} since last save")
    
    if since_last >= SAVE_INTERVAL and exchange_count > 0:
        state.last_save = exchange_count
        state.save()
        
        # Extract and accumulate summary
        summary = process_summary(DIARY_DIR, session_id)
        
        if is_verbose_mode():
            output_block_with_summary(summary)
        else:
            output_empty()
    else:
        output_empty()
```

**移除的 mempalace 功能：**
- ❌ `mempalace mine` 命令调用
- ❌ `MEMPAL_DIR` 配置项
- ❌ 所有 vector DB/GPU 相关逻辑

### state.py - Hook State 管理

```python
from pathlib import Path
from datetime import datetime
from .config import STATE_DIR

class HookState:
    """Manage hook state for a session
    
    State directory: ~/.session-diary/hook_state/
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state_dir = STATE_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.last_save_file = self.state_dir / f"{session_id}_last_save.txt"
        self.log_file = self.state_dir / "hook.log"
        
        self.last_save = self._read_last_save()
    
    def _read_last_save(self) -> int:
        if not self.last_save_file.exists():
            return 0
        try:
            content = self.last_save_file.read_text().strip()
            if content.isdigit():
                return int(content)
            return 0
        except Exception:
            return 0
    
    def save(self):
        self.last_save_file.write_text(str(self.last_save))
    
    def log(self, message: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        self.log_file.write_text(log_entry, append=True)
```

### config.py - 配置常量

```python
from pathlib import Path
import os

# Save interval: every N human messages
SAVE_INTERVAL = int(os.getenv('SESSION_DIARY_SAVE_INTERVAL', '15'))

# State directory (hook state files, logs)
STATE_DIR = Path(os.getenv('SESSION_DIARY_STATE_DIR', '~/.session-diary/hook_state')).expanduser()

# Diary directory (session diary markdown files)
DIARY_DIR = Path(os.getenv('SESSION_DIARY_MEMORY_DIR', '.session-memory'))

# Verbose mode
VERBOSE_MODE = os.getenv('SESSION_DIARY_VERBOSE', 'false').lower() in ('true', '1', 'yes')

# Size limit for summary section (30KB)
MAX_SUMMARY_SIZE = 30720

# Max entries to keep when trimming
MAX_SUMMARY_ENTRIES = 6
```

### sessionstart_hook.py - SessionStart Hook

```python
from pathlib import Path
from .extractor import extract_summary_section
from .config import DIARY_DIR

def main():
    """SessionStart hook: inject project memory into system prompt"""
    diary_dir = DIARY_DIR
    latest_diary = find_latest_diary(diary_dir)
    
    if not latest_diary:
        output_no_diary_fallback()
        return
    
    summary_section = extract_summary_section(latest_diary)
    
    if summary_section:
        output_new_format(latest_diary, summary_section)
    else:
        output_old_format(diary_dir)


def find_latest_diary(diary_dir: Path) -> Path | None:
    """Find latest diary file by filename (descending)"""
    if not diary_dir.exists():
        return None
    
    files = sorted(
        diary_dir.glob(".session-diary-*.md"),
        key=lambda p: p.name,
        reverse=True
    )
    
    return files[0] if files else None
```

### installer.py - 自动配置助手

```python
import json
from pathlib import Path

def main():
    """Auto-configure Claude Code settings.json
    
    Usage: session-diary-install
    """
    print("🔧 Session Diary Plugin Installer")
    
    settings_path = find_settings_json()
    
    if not settings_path:
        print("❌ Claude Code config not found")
        print("   Expected: .claude/settings.local.json")
        return
    
    print(f"✅ Found config: {settings_path}")
    
    config = read_settings(settings_path)
    
    if hooks_already_configured(config):
        print("⚠️  Hooks already configured")
        return
    
    config = add_hooks(config)
    write_settings(settings_path, config)
    
    print("✅ Hooks configured successfully")
    print("⚠️  IMPORTANT: Requires Claude Code restart")


def find_settings_json() -> Path | None:
    """Find Claude Code settings file"""
    candidates = [
        Path(".claude/settings.local.json"),
        Path(".claude/settings.json"),
        Path.home() / ".claude/settings.local.json",
    ]
    
    for path in candidates:
        if path.exists():
            return path
    
    return None


def add_hooks(config: dict) -> dict:
    """Add session diary hooks to config"""
    config.setdefault("hooks", {})
    
    config["hooks"]["Stop"] = [{
        "matcher": "*",
        "hooks": [{
            "type": "command",
            "command": "session-diary-save-hook",
            "timeout": 30
        }]
    }]
    
    config["hooks"]["SessionStart"] = [{
        "matcher": "*",
        "hooks": [{
            "type": "command",
            "command": "session-diary-sessionstart-hook",
            "timeout": 10
        }]
    }]
    
    return config
```

---

## Claude Code 集成方案

### uv tool 安装机制

在 `pyproject.toml` 中配置 console_scripts：

```toml
[project.scripts]
session-diary-save-hook = "session_diary.save_hook:main"
session-diary-sessionstart-hook = "session_diary.sessionstart_hook:main"
session-diary-install = "session_diary.installer:main"
```

**安装流程：**

```bash
# 1. 安装
uv tool install session-diary-plugin

# 2. 验证
uv tool list
which session-diary-save-hook

# 3. 配置
session-diary-install

# 4. 重启 Claude Code
```

**配置示例：**

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "session-diary-save-hook",  // PATH 命令
        "timeout": 30
      }]
    }],
    "SessionStart": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "session-diary-sessionstart-hook",
        "timeout": 10
      }]
    }]
  }
}
```

**优势：**
- 无需绝对路径配置
- 跨平台统一
- 自动发现可执行文件

---

## 测试策略

### 测试文件结构

```
tests/
├── conftest.py               # 共享 fixtures
├── test_extractor.py         # 测试 summary extraction
├── test_counter.py           # 测试 message counting
├── test_save_hook.py         # 测试 save hook
├── test_sessionstart_hook.py
├── test_state.py
└── test_installer.py
```

### Fixtures 示例

```python
@pytest.fixture
def sample_diary_new_format():
    """Sample diary with summary section"""
    content = """# Session Diary - 2026-05-02 18:33

## 历史任务摘要（截止本次会话）

### 2026-05-02 18:33 Sample Task
- **成果：** Test extraction
- **决策：** Use Python

---

## 本次进展

### Sample Task

Content...

## 关键发现

- Finding 1
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        yield Path(f.name)
    Path(f.name).unlink()
```

### 测试示例

```python
def test_extract_summary_section_new_format(sample_diary_new_format):
    result = extract_summary_section(sample_diary_new_format)
    
    assert "## 历史任务摘要" in result
    assert "### 2026-05-02 18:33 Sample Task" in result
    assert "---" in result


def test_accumulate_and_trim_summary_over_limit():
    # Create large summary (over 30KB)
    old_summary = "## 历史任务摘要\n\n" + "\n".join([
        f"### Entry {i}\n- Item {i}"
        for i in range(1, 100)
    ]) + "\n\n---"
    
    new_entry = "### New Entry\n- Item new"
    result = accumulate_and_trim_summary(old_summary, new_entry)
    
    # Should keep only 6 entries
    assert "New Entry" in result
    assert "Entry 98" in result
    assert "Entry 92" not in result
```

**覆盖率目标：** 80%+

---

## 迁移方案

### 数据迁移（无需操作）

| 项目 | MemPalace | Session Diary Plugin | 迁移策略 |
|------|-----------|---------------------|----------|
| Diary 文件 | `.session-memory/*.md` | `.session-memory/*.md` | ✅ 保持不变 |
| Diary 格式 | 新旧混合 | 新旧混合兼容 | ✅ 自动兼容 |
| Hook state | `~/.mempalace/hook_state/` | `~/.session-diary/hook_state/` | 新路径，旧数据可忽略 |

### Hooks 配置迁移

**迁移步骤：**

```bash
# 1. 安装新包
uv tool install session-diary-plugin

# 2. 运行配置助手（自动覆盖）
session-diary-install

# 3. 清理旧 wrapper（可选）
rm ~/.claude/hooks/mempal-*.sh

# 4. 重启 Claude Code
```

### 功能差异对比

| 功能 | MemPalace | Session Diary Plugin | 影响 |
|------|-----------|---------------------|------|
| Session diary | ✅ | ✅ | 无变化 |
| Summary extraction | ✅ | ✅ | 无变化 |
| SessionStart injection | ✅ | ✅ | 无变化 |
| `mempalace mine` | ✅ | ❌ | 不再自动挖掘 |
| Vector search | ✅ | ❌ | 不支持语义搜索 |
| Entity KG | ✅ | ❌ | 不支持知识图谱 |
| GPU/Qdrant | ✅ | ❌ | 零资源占用 |

**用户需知：**
- ❌ 不再支持自动挖掘对话历史
- ❌ 不支持语义搜索
- ✅ Session diary 功能完全保留

---

## pyproject.toml 配置

```toml
[project]
name = "session-diary-plugin"
version = "1.0.0"
description = "Lightweight session diary hooks for Claude Code - zero dependencies"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
requires-python = ">=3.8"

dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]

[project.scripts]
session-diary-save-hook = "session_diary.save_hook:main"
session-diary-sessionstart-hook = "session_diary.sessionstart_hook:main"
session-diary-install = "session_diary.installer:main"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=session_diary --cov-report=term-missing"

[tool.coverage.report]
fail_under = 80
```

---

## README.md 文档

见独立 README.md 文件，包含：
- 问题背景与解决方案
- Installation（uv tool）
- How It Works（Stop hook + SessionStart hook）
- Configuration（环境变量）
- Migration from MemPalace
- Development

---

## 设计决策

### 为什么选择纯 Python Hooks？

1. **测试性更好**：现有 bash 测试复杂（source、assert output），Python 直接 import + pytest
2. **维护成本低**：单一语言，无 bash/Python 混合逻辑
3. **跨平台**：Windows/macOS/Linux 统一行为
4. **安装简单**：uv tool 后 hooks 自动在 PATH
5. **代码清晰**：现有 bash 352行，eval/shell injection 防护复杂，Python 更简洁

### 为什么选择 uv tool 安装？

1. **符合项目规范**：项目已使用 uv 管理 Python
2. **简单安装**：一条命令 `uv tool install`
3. **自动配置**：可执行文件注册到 PATH
4. **隔离安全**：独立环境，不影响系统 Python
5. **易于更新**：`uv tool upgrade`

### 为什么移除 mempalace mine？

- 需要依赖 vector DB + GPU（重型资源）
- 与 session diary 功能独立
- 用户可手动保存关键内容

---

## 下一步

设计完成，等待用户 review。通过后进入 writing-plans skill 创建实施计划。