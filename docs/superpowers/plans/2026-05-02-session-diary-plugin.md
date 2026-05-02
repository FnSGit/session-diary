# Session Diary Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build lightweight session diary plugin for Claude Code - zero dependencies, zero vector DB, pure Python hooks with uv tool installation.

**Architecture:** 7 core Python modules (config → counter → extractor → state → save_hook → sessionstart_hook → installer), TDD workflow, pytest 80% coverage, console_scripts registered via pyproject.toml.

**Tech Stack:** Python 3.8+ (standard library only: json, pathlib, re, datetime), pytest, uv tool installation.

---

## Task 1: Project Initialization

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `LICENSE`
- Create: `session_diary/` directory
- Create: `tests/` directory

- [ ] **Step 1: Create project directory structure**

Run:
```bash
mkdir -p session_diary tests
```

- [ ] **Step 2: Write pyproject.toml**

Create `pyproject.toml`:
```toml
[project]
name = "session-diary-plugin"
version = "1.0.0"
description = "Lightweight session diary hooks for Claude Code - zero dependencies, zero vector DB"
authors = [{name = "Feng Shuai", email = "your.email@example.com"}]
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

[tool.setuptools.packages.find]
where = ["."]
include = ["session_diary"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --cov=session_diary --cov-report=term-missing"

[tool.coverage.run]
source = ["session_diary"]
omit = ["tests/*"]

[tool.coverage.report]
fail_under = 80
```

- [ ] **Step 3: Write README.md**

Create `README.md`:
```markdown
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
```

- [ ] **Step 4: Write LICENSE**

Create `LICENSE`:
```
MIT License

Copyright (c) 2026 Feng Shuai

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 5: Commit project initialization**

Run:
```bash
git add pyproject.toml README.md LICENSE session_diary/ tests/
git commit -m "init: project structure with pyproject.toml, README, LICENSE"
```

---

## Task 2: config.py - Configuration Constants

**Files:**
- Create: `session_diary/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing test for config constants**

Create `tests/test_config.py`:
```python
import os
from pathlib import Path
from session_diary import config


def test_default_save_interval():
    """Test default SAVE_INTERVAL is 15"""
    assert config.SAVE_INTERVAL == 15


def test_default_state_dir():
    """Test default STATE_DIR is ~/.session-diary/hook_state"""
    expected = Path.home() / ".session-diary" / "hook_state"
    assert config.STATE_DIR == expected


def test_default_diary_dir():
    """Test default DIARY_DIR is .session-memory"""
    assert config.DIARY_DIR == Path(".session-memory")


def test_default_verbose_mode():
    """Test default VERBOSE_MODE is False"""
    assert config.VERBOSE_MODE is False


def test_env_override_save_interval():
    """Test SESSION_DIARY_SAVE_INTERVAL env override"""
    os.environ['SESSION_DIARY_SAVE_INTERVAL'] = '10'

    # Reload config to pick up env var
    import importlib
    importlib.reload(config)

    assert config.SAVE_INTERVAL == 10

    # Clean up
    del os.environ['SESSION_DIARY_SAVE_INTERVAL']


def test_env_override_verbose_mode():
    """Test SESSION_DIARY_VERBOSE env override"""
    os.environ['SESSION_DIARY_VERBOSE'] = 'true'

    import importlib
    importlib.reload(config)

    assert config.VERBOSE_MODE is True

    del os.environ['SESSION_DIARY_VERBOSE']
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_config.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'session_diary'"

- [ ] **Step 3: Write config.py implementation**

Create `session_diary/config.py`:
```python
"""Configuration constants for session diary plugin

All constants can be overridden via environment variables.
"""
from pathlib import Path
import os

# Save interval: every N human messages
SAVE_INTERVAL = int(os.getenv('SESSION_DIARY_SAVE_INTERVAL', '15'))

# State directory (hook state files, logs)
STATE_DIR = Path(os.getenv('SESSION_DIARY_STATE_DIR', '~/.session-diary/hook_state')).expanduser()

# Diary directory (session diary markdown files)
# Default: .session-memory/ relative to project root
DIARY_DIR = Path(os.getenv('SESSION_DIARY_MEMORY_DIR', '.session-memory'))

# Verbose mode: block and show diaries in chat (true) or silent mode (false)
VERBOSE_MODE = os.getenv('SESSION_DIARY_VERBOSE', 'false').lower() in ('true', '1', 'yes')

# Size limit for summary section (30KB)
MAX_SUMMARY_SIZE = 30720  # bytes

# Max entries to keep when trimming
MAX_SUMMARY_ENTRIES = 6  # new entry + 5 newest old entries
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_config.py -v
```

Expected: PASS (7 tests)

- [ ] **Step 5: Commit config module**

Run:
```bash
git add session_diary/config.py tests/test_config.py
git commit -m "feat(config): add configuration constants with env override support"
```

---

## Task 3: counter.py - Message Counting

**Files:**
- Create: `session_diary/counter.py`
- Create: `tests/test_counter.py`
- Create: `tests/conftest.py` (fixtures)

- [ ] **Step 1: Write fixtures in conftest.py**

Create `tests/conftest.py`:
```python
"""Shared fixtures for session diary tests"""
import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def sample_transcript():
    """Sample JSONL transcript with 5 user messages (excluding command messages)"""
    content = """
{"message": {"role": "user", "content": "Hello"}}
{"message": {"role": "assistant", "content": "Hi"}}
{"message": {"role": "user", "content": "Question 1"}}
{"message": {"role": "assistant", "content": "Answer 1"}}
{"message": {"role": "user", "content": "Question 2"}}
{"message": {"role": "assistant", "content": "Answer 2"}}
{"message": {"role": "user", "content": "<command-message>skip this</command-message>"}}
{"message": {"role": "user", "content": "Question 3"}}
{"message": {"role": "assistant", "content": "Answer 3"}}
{"message": {"role": "user", "content": "Question 4"}}
{"message": {"role": "assistant", "content": "Answer 4"}}
{"message": {"role": "user", "content": "Question 5"}}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(content)
        yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def empty_transcript():
    """Empty JSONL transcript"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write("")
        yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def malformed_transcript():
    """JSONL transcript with malformed JSON"""
    content = """
{"message": {"role": "user", "content": "Valid"}}
{invalid json here}
{"message": {"role": "user", "content": "Also valid"}}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(content)
        yield Path(f.name)
    Path(f.name).unlink()
```

- [ ] **Step 2: Write failing test for counter**

Create `tests/test_counter.py`:
```python
from session_diary.counter import count_human_messages


def test_count_human_messages_basic(sample_transcript):
    """Test counting user messages in basic transcript"""
    result = count_human_messages(sample_transcript)
    # Should count 5 user messages (excluding 1 command message)
    assert result == 5


def test_count_human_messages_empty(empty_transcript):
    """Test counting messages in empty transcript"""
    result = count_human_messages(empty_transcript)
    assert result == 0


def test_count_human_messages_malformed(malformed_transcript):
    """Test counting messages handles malformed JSON gracefully"""
    result = count_human_messages(malformed_transcript)
    # Should count 2 valid user messages, skip malformed line
    assert result == 2


def test_count_human_messages_nonexistent_file():
    """Test counting messages when file doesn't exist"""
    from pathlib import Path
    nonexistent = Path("/nonexistent/file.jsonl")
    result = count_human_messages(nonexistent)
    # Should handle gracefully and return 0
    assert result == 0
```

- [ ] **Step 3: Run test to verify it fails**

Run:
```bash
pytest tests/test_counter.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'session_diary.counter'"

- [ ] **Step 4: Write counter.py implementation**

Create `session_diary/counter.py`:
```python
"""Count human messages in JSONL transcript files"""
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

    # Handle nonexistent file gracefully
    if not transcript_path.exists():
        return 0

    try:
        with transcript_path.open('r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    msg = entry.get('message', {})

                    # Only count user role
                    if isinstance(msg, dict) and msg.get('role') == 'user':
                        content = msg.get('content', '')

                        # Skip command messages (e.g., <command-message>)
                        if isinstance(content, str) and '<command-message>' in content:
                            continue

                        count += 1
                except json.JSONDecodeError:
                    # Skip malformed lines gracefully
                    continue
    except Exception:
        # Handle file read errors gracefully
        return 0

    return count
```

- [ ] **Step 5: Run test to verify it passes**

Run:
```bash
pytest tests/test_counter.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 6: Commit counter module**

Run:
```bash
git add session_diary/counter.py tests/test_counter.py tests/conftest.py
git commit -m "feat(counter): add message counting from JSONL transcripts"
```

---

## Task 4: extractor.py - Summary Extraction (Part 1: extract_summary_section)

**Files:**
- Create: `session_diary/extractor.py`
- Create: `tests/test_extractor.py`
- Modify: `tests/conftest.py` (add diary fixtures)

- [ ] **Step 1: Add diary fixtures to conftest.py**

Modify `tests/conftest.py`, add after existing fixtures:
```python
@pytest.fixture
def sample_diary_new_format():
    """Sample diary with summary section (new format)"""
    content = """# Session Diary - 2026-05-02 18:33

## 历史任务摘要（截止本次会话）

### 2026-05-02 18:33 Sample Task
- **成果：** Test extraction, summary generation
- **决策：** Use Python instead of bash

---

## 本次进展

### Sample Task Implementation

Content here...

## 关键发现

- Finding 1
- Finding 2

## 关键决策

**决策 1: Use Python**
- Reason: Better testability
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def sample_diary_old_format():
    """Sample diary without summary (old format)"""
    content = """# Session Diary - 2026-05-01 10:00

## 本次进展

Old format content...

## 关键发现

- Old finding
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def sample_diary_no_end_marker():
    """Sample diary with summary but no end marker"""
    content = """# Session Diary - 2026-05-02 20:00

## 历史任务摘要（截止本次会话）

### 2026-05-02 20:00 Task Without End
- **成果：** No separator
- **决策：** Continue to end of file

## 本次进展

Content continues without --- separator
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        yield Path(f.name)
    Path(f.name).unlink()
```

- [ ] **Step 2: Write failing test for extract_summary_section**

Create `tests/test_extractor.py`:
```python
from session_diary.extractor import extract_summary_section


def test_extract_summary_section_new_format(sample_diary_new_format):
    """Test extraction from new format diary"""
    result = extract_summary_section(sample_diary_new_format)

    assert "## 历史任务摘要" in result
    assert "### 2026-05-02 18:33 Sample Task" in result
    assert "- **成果：** Test extraction, summary generation" in result
    assert "- **决策：** Use Python instead of bash" in result
    assert "---" in result


def test_extract_summary_section_old_format(sample_diary_old_format):
    """Test extraction from old format diary (should return empty)"""
    result = extract_summary_section(sample_diary_old_format)

    assert result == ""


def test_extract_summary_section_no_end_marker(sample_diary_no_end_marker):
    """Test extraction when no --- end marker exists"""
    result = extract_summary_section(sample_diary_no_end_marker)

    assert "## 历史任务摘要" in result
    assert "### 2026-05-02 20:00 Task Without End" in result
    # Should return rest of file when no end marker
    assert "Content continues without --- separator" in result


def test_extract_summary_section_nonexistent_file():
    """Test extraction when file doesn't exist"""
    from pathlib import Path
    nonexistent = Path("/nonexistent/diary.md")
    result = extract_summary_section(nonexistent)

    assert result == ""
```

- [ ] **Step 3: Run test to verify it fails**

Run:
```bash
pytest tests/test_extractor.py::test_extract_summary_section_new_format -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'session_diary.extractor'"

- [ ] **Step 4: Write extractor.py (Part 1: extract_summary_section)**

Create `session_diary/extractor.py`:
```python
"""Extract summary sections from session diaries"""
from pathlib import Path


def extract_summary_section(diary_path: Path) -> str:
    """Extract summary section from diary file

    Args:
        diary_path: Path to .session-diary-*.md file

    Returns:
        Summary section content (from "## 历史任务摘要" to "---")
        Empty string if not found
    """
    # Handle nonexistent file
    if not diary_path.exists():
        return ""

    try:
        content = diary_path.read_text()

        start_marker = "## 历史任务摘要"
        end_marker = "---"

        start_idx = content.find(start_marker)
        if start_idx == -1:
            return ""

        end_idx = content.find(end_marker, start_idx)
        if end_idx == -1:
            # No end marker, return rest of file
            return content[start_idx:]

        return content[start_idx:end_idx + len(end_marker)]
    except Exception:
        return ""
```

- [ ] **Step 5: Run test to verify it passes**

Run:
```bash
pytest tests/test_extractor.py -v
```

Expected: PASS (4 tests for extract_summary_section)

- [ ] **Step 6: Commit extractor Part 1**

Run:
```bash
git add session_diary/extractor.py tests/test_extractor.py tests/conftest.py
git commit -m "feat(extractor): add extract_summary_section function"
```

---

## Task 5: extractor.py - Summary Extraction (Part 2: generate_current_entry)

**Files:**
- Modify: `session_diary/extractor.py`
- Modify: `tests/test_extractor.py`

- [ ] **Step 1: Write failing test for generate_current_entry**

Modify `tests/test_extractor.py`, add after existing tests:
```python
from session_diary.extractor import generate_current_entry


def test_generate_current_entry_basic(sample_diary_new_format):
    """Test basic current entry generation"""
    result = generate_current_entry(sample_diary_new_format, "2026-05-02 20:00")

    assert "### 2026-05-02 20:00" in result
    assert "**成果：**" in result
    assert "**决策：**" in result
    # Should extract task title from first ### in "## 本次进展"
    assert "Sample Task Implementation" in result


def test_generate_current_entry_empty_diary():
    """Test generation when diary is empty"""
    from pathlib import Path
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Empty Diary\n")
        empty_diary = Path(f.name)

    result = generate_current_entry(empty_diary, "2026-05-02 21:00")

    # Should handle gracefully with placeholders
    assert "### 2026-05-02 21:00" in result
    assert "**成果：** （待补充）" in result
    assert "**决策：** （待补充）" in result

    empty_diary.unlink()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_extractor.py::test_generate_current_entry_basic -v
```

Expected: FAIL with "ImportError: cannot import name 'generate_current_entry'"

- [ ] **Step 3: Write generate_current_entry implementation**

Modify `session_diary/extractor.py`, add after `extract_summary_section`:
```python
def extract_first_task_title(content: str) -> str:
    """Extract first task title from '## 本次进展' section

    Args:
        content: Full diary content

    Returns:
        Task title (first ### header in 本次进展 section)
        Empty string if not found
    """
    # Find "## 本次进展" section
    start_idx = content.find("## 本次进展")
    if start_idx == -1:
        return ""

    # Find next ## section (end boundary)
    end_idx = content.find("\n## ", start_idx + len("## 本次进展"))
    if end_idx == -1:
        section_content = content[start_idx:]
    else:
        section_content = content[start_idx:end_idx]

    # Find first ### header
    title_idx = section_content.find("### ")
    if title_idx == -1:
        return ""

    # Extract title (until newline)
    title_start = title_idx + len("### ")
    title_end = section_content.find("\n", title_start)
    if title_end == -1:
        return section_content[title_start:].strip()

    return section_content[title_start:title_end].strip()


def extract_outcomes(content: str, max_count: int = 5) -> str:
    """Extract outcomes from '## 关键发现' section

    Args:
        content: Full diary content
        max_count: Maximum bullets to extract

    Returns:
        Comma-separated outcomes
    """
    # Find "## 关键发现" section
    start_idx = content.find("## 关键发现")
    if start_idx == -1:
        return "（待补充）"

    # Find next ## section
    end_idx = content.find("\n## ", start_idx + len("## 关键发现"))
    if end_idx == -1:
        section_content = content[start_idx:]
    else:
        section_content = content[start_idx:end_idx]

    # Extract bullet points
    bullets = []
    for line in section_content.split("\n"):
        if line.startswith("- ") and not line.startswith("- **成果") and not line.startswith("- **决策"):
            bullets.append(line[2:].strip())
            if len(bullets) >= max_count:
                break

    return ", ".join(bullets) if bullets else "（待补充）"


def extract_decisions(content: str, max_count: int = 3) -> str:
    """Extract decisions from '## 关键决策' section

    Args:
        content: Full diary content
        max_count: Maximum decisions to extract

    Returns:
        Comma-separated decision titles
    """
    # Find "## 关键决策" section
    start_idx = content.find("## 关键决策")
    if start_idx == -1:
        return "（待补充）"

    # Find next ## section
    end_idx = content.find("\n## ", start_idx + len("## 关键决策"))
    if end_idx == -1:
        section_content = content[start_idx:]
    else:
        section_content = content[start_idx:end_idx]

    # Extract decision titles
    decisions = []
    for line in section_content.split("\n"):
        if line.startswith("**决策") and ":" in line:
            # Extract title between **决策N: title**
            colon_idx = line.find(":")
            if colon_idx != -1:
                title_start = colon_idx + 1
                title_end = line.find("**", title_start)
                if title_end != -1:
                    title = line[title_start:title_end].strip()
                    decisions.append(title)
                    if len(decisions) >= max_count:
                        break

    return ", ".join(decisions) if decisions else "（待补充）"


def generate_current_entry(diary_path: Path, timestamp: str) -> str:
    """Generate current session summary entry

    Args:
        diary_path: Path to current diary
        timestamp: "YYYY-MM-DD HH:MM" format

    Returns:
        Formatted entry: "### YYYY-MM-DD HH:MM Task Title\n- **成果：** ...\n- **决策：** ..."
    """
    if not diary_path.exists():
        return f"### {timestamp} Session Diary\n- **成果：** （待补充）\n- **决策：** （待补充）"

    try:
        content = diary_path.read_text()

        # Extract components
        task_title = extract_first_task_title(content)
        outcomes = extract_outcomes(content, max_count=5)
        decisions = extract_decisions(content, max_count=3)

        # Format entry
        return f"### {timestamp} {task_title}\n- **成果：** {outcomes}\n- **决策：** {decisions}"
    except Exception:
        return f"### {timestamp} Session Diary\n- **成果：** （待补充）\n- **决策：** （待补充）"
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_extractor.py::test_generate_current_entry -v
```

Expected: PASS (2 tests for generate_current_entry)

- [ ] **Step 5: Commit extractor Part 2**

Run:
```bash
git add session_diary/extractor.py tests/test_extractor.py
git commit -m "feat(extractor): add generate_current_entry with helper functions"
```

---

## Task 6: extractor.py - Summary Extraction (Part 3: accumulate_and_trim_summary)

**Files:**
- Modify: `session_diary/extractor.py`
- Modify: `tests/test_extractor.py`

- [ ] **Step 1: Write failing test for accumulate_and_trim_summary**

Modify `tests/test_extractor.py`, add after existing tests:
```python
from session_diary.extractor import accumulate_and_trim_summary


def test_accumulate_and_trim_summary_under_limit():
    """Test accumulation when under 30KB size limit"""
    old_summary = "## 历史任务摘要（截止本次会话）\n\n### Entry 1\n- Item 1\n\n---"
    new_entry = "### 2026-05-02 20:00 New Entry\n- Item new"

    result = accumulate_and_trim_summary(old_summary, new_entry)

    assert "### 2026-05-02 20:00 New Entry" in result
    assert "### Entry 1" in result
    assert "## 历史任务摘要（截止本次会话）" in result
    assert "---" in result


def test_accumulate_and_trim_summary_over_limit():
    """Test trimming when over 30KB limit"""
    # Create large summary (over 30KB)
    entries = []
    for i in range(1, 100):
        entries.append(f"### 2026-05-01 {i:02d}:00 Entry {i}\n- Item {i}\n- Detail {i}")

    old_summary = "## 历史任务摘要（截止本次会话）\n\n" + "\n\n".join(entries) + "\n\n---"

    # Verify old summary is over 30KB
    assert len(old_summary.encode('utf-8')) > 30720

    new_entry = "### 2026-05-02 20:00 New Entry\n- Item new"
    result = accumulate_and_trim_summary(old_summary, new_entry)

    # Should keep new entry + 5 newest old entries (total 6)
    assert "### 2026-05-02 20:00 New Entry" in result
    assert "### 2026-05-01 99:00 Entry 99" in result  # newest old
    assert "### 2026-05-01 95:00 Entry 95" in result  # 5th newest old
    assert "### 2026-05-01 94:00 Entry 94" not in result  # trimmed

    # Result should be under 30KB
    assert len(result.encode('utf-8')) <= 30720


def test_accumulate_and_trim_summary_empty_old():
    """Test accumulation when old summary is empty"""
    old_summary = ""
    new_entry = "### 2026-05-02 20:00 New Entry\n- Item new"

    result = accumulate_and_trim_summary(old_summary, new_entry)

    assert "### 2026-05-02 20:00 New Entry" in result
    assert "## 历史任务摘要（截止本次会话）" in result
    assert "---" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_extractor.py::test_accumulate_and_trim_summary_under_limit -v
```

Expected: FAIL with "ImportError: cannot import name 'accumulate_and_trim_summary'"

- [ ] **Step 3: Write accumulate_and_trim_summary implementation**

Modify `session_diary/extractor.py`, add after `generate_current_entry`:
```python
def remove_summary_metadata(summary: str) -> str:
    """Remove header and separator from summary

    Args:
        summary: Full summary section

    Returns:
        Content without header line and --- separator
    """
    lines = summary.split("\n")

    # Remove first line (header)
    if lines and lines[0].startswith("## 历史任务摘要"):
        lines = lines[1:]

    # Remove --- separator
    lines = [line for line in lines if line.strip() != "---"]

    return "\n".join(lines).strip()


def extract_summary_entries(summary: str) -> list:
    """Extract individual entries from summary

    Args:
        summary: Full summary section

    Returns:
        List of entry strings (each starts with "### ")
    """
    entries = []
    current_entry = []

    for line in summary.split("\n"):
        if line.startswith("### "):
            if current_entry:
                entries.append("\n".join(current_entry))
            current_entry = [line]
        else:
            if current_entry:
                current_entry.append(line)

    if current_entry:
        entries.append("\n".join(current_entry))

    return entries


def rebuild_summary(entries: list) -> str:
    """Rebuild summary from entries list

    Args:
        entries: List of entry strings

    Returns:
        Full summary section with header and separator
    """
    content = "\n\n".join(entries)
    return f"## 历史任务摘要（截止本次会话）\n\n{content}\n\n---"


def accumulate_and_trim_summary(old_summary: str, new_entry: str) -> str:
    """Accumulate and trim summary entries (size control: 30KB)

    Args:
        old_summary: Full summary section content
        new_entry: New entry to prepend

    Returns:
        Combined summary with size control (max 30KB, trim oldest entries if exceeded)
    """
    from .config import MAX_SUMMARY_SIZE, MAX_SUMMARY_ENTRIES

    # Remove header and separator from old content
    old_content = remove_summary_metadata(old_summary)

    # Build new summary: header + new_entry + old_content + separator
    if old_content:
        new_summary = f"## 历史任务摘要（截止本次会话）\n\n{new_entry}\n\n{old_content}\n\n---"
    else:
        new_summary = f"## 历史任务摘要（截止本次会话）\n\n{new_entry}\n\n---"

    # Check size (30KB = 30720 bytes)
    if len(new_summary.encode('utf-8')) > MAX_SUMMARY_SIZE:
        # Extract entries
        entries = extract_summary_entries(new_summary)

        if len(entries) > MAX_SUMMARY_ENTRIES:
            # Keep new entry + 5 newest old entries (total 6)
            trimmed_entries = entries[:MAX_SUMMARY_ENTRIES]
            new_summary = rebuild_summary(trimmed_entries)

    return new_summary
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_extractor.py -v
```

Expected: PASS (all extractor tests, total ~10 tests)

- [ ] **Step 5: Commit extractor Part 3**

Run:
```bash
git add session_diary/extractor.py tests/test_extractor.py
git commit -m "feat(extractor): add accumulate_and_trim_summary with size control"
```

---

## Task 7: state.py - Hook State Management

**Files:**
- Create: `session_diary/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 1: Write failing test for HookState**

Create `tests/test_state.py`:
```python
from pathlib import Path
from session_diary.state import HookState


def test_hook_state_init():
    """Test HookState initialization"""
    state = HookState("test_session_123")

    assert state.session_id == "test_session_123"
    assert state.last_save == 0


def test_hook_state_save_and_read():
    """Test saving and reading last_save count"""
    state = HookState("test_session_456")

    state.last_save = 15
    state.save()

    # Create new instance to test reading
    state2 = HookState("test_session_456")
    assert state2.last_save == 15

    # Clean up
    state2.last_save_file.unlink()


def test_hook_state_log():
    """Test logging messages"""
    state = HookState("test_session_789")

    state.log("Test message 1")
    state.log("Test message 2")

    # Verify log file exists and contains messages
    assert state.log_file.exists()

    content = state.log_file.read_text()
    assert "Test message 1" in content
    assert "Test message 2" in content

    # Clean up
    state.log_file.unlink()
    state.state_dir.rmdir()


def test_hook_state_invalid_last_save():
    """Test handling invalid last_save file content"""
    state = HookState("test_session_invalid")

    # Write invalid content
    state.last_save_file.write_text("not_a_number")

    # Create new instance to test validation
    state2 = HookState("test_session_invalid")
    assert state2.last_save == 0  # Should default to 0 for invalid content

    # Clean up
    state2.last_save_file.unlink()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_state.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'session_diary.state'"

- [ ] **Step 3: Write state.py implementation**

Create `session_diary/state.py`:
```python
"""Manage hook state for sessions"""
from pathlib import Path
from datetime import datetime
from .config import STATE_DIR


class HookState:
    """Manage hook state for a session

    State directory: ~/.session-diary/hook_state/
    State file: {session_id}_last_save.txt
    Log file: hook.log
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state_dir = STATE_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.last_save_file = self.state_dir / f"{session_id}_last_save.txt"
        self.log_file = self.state_dir / "hook.log"

        self.last_save = self._read_last_save()

    def _read_last_save(self) -> int:
        """Read last save count from file"""
        if not self.last_save_file.exists():
            return 0

        try:
            content = self.last_save_file.read_text().strip()
            # Validate as integer (security: prevent command injection)
            if content.isdigit():
                return int(content)
            return 0
        except Exception:
            return 0

    def save(self):
        """Save current state to file"""
        self.last_save_file.write_text(str(self.last_save))

    def log(self, message: str):
        """Append log message to hook.log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"

        # Append to log file
        with self.log_file.open('a') as f:
            f.write(log_entry)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_state.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit state module**

Run:
```bash
git add session_diary/state.py tests/test_state.py
git commit -m "feat(state): add hook state management with logging"
```

---

## Task 8: save_hook.py - Stop Hook Main Logic

**Files:**
- Create: `session_diary/save_hook.py`
- Create: `tests/test_save_hook.py`

- [ ] **Step 1: Write failing test for save_hook**

Create `tests/test_save_hook.py`:
```python
import json
from io import StringIO
from session_diary import save_hook


def test_save_hook_empty_json():
    """Test save_hook with empty JSON (should output {} and exit)"""
    # Mock stdin
    input_data = {}

    # Capture stdout
    import sys
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    # Mock stdin
    sys.stdin = StringIO(json.dumps(input_data))

    try:
        save_hook.main()
        output = sys.stdout.getvalue()
        result = json.loads(output)

        # Should output empty JSON (not time to save)
        assert result == {}
    finally:
        sys.stdout = old_stdout


def test_save_hook_stop_hook_active():
    """Test save_hook when stop_hook_active=True (infinite loop prevention)"""
    input_data = {
        "session_id": "test_123",
        "stop_hook_active": True,
        "transcript_path": "/tmp/test.jsonl"
    }

    import sys
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    sys.stdin = StringIO(json.dumps(input_data))

    try:
        save_hook.main()
        output = sys.stdout.getvalue()
        result = json.loads(output)

        # Should output {} (let AI stop)
        assert result == {}
    finally:
        sys.stdout = old_stdout


def test_save_hook_missing_transcript():
    """Test save_hook when transcript_path is missing"""
    input_data = {
        "session_id": "test_456",
        "stop_hook_active": False
        # Missing transcript_path
    }

    import sys
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    sys.stdin = StringIO(json.dumps(input_data))

    try:
        save_hook.main()
        output = sys.stdout.getvalue()
        result = json.loads(output)

        # Should handle gracefully
        assert result == {}
    finally:
        sys.stdout = old_stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_save_hook.py::test_save_hook_empty_json -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'session_diary.save_hook'"

- [ ] **Step 3: Write save_hook.py implementation (Part 1: main structure)**

Create `session_diary/save_hook.py`:
```python
"""Stop hook main logic - triggers diary saves every N messages"""
import json
import sys
from pathlib import Path
from datetime import datetime
from .counter import count_human_messages
from .extractor import extract_summary_section, generate_current_entry, accumulate_and_trim_summary
from .state import HookState
from .config import SAVE_INTERVAL, DIARY_DIR, VERBOSE_MODE


def read_stdin_json() -> dict:
    """Read JSON input from stdin

    Returns:
        dict with session_id, stop_hook_active, transcript_path
    """
    try:
        input_text = sys.stdin.read()
        return json.loads(input_text)
    except json.JSONDecodeError:
        return {}


def output_empty():
    """Output empty JSON to let AI stop normally"""
    print("{}")


def output_block_with_summary(summary: str):
    """Output block decision with summary

    Args:
        summary: Pending summary to inject
    """
    # Escape newlines for JSON
    summary_escaped = summary.replace("\n", "\\n")

    block_json = {
        "decision": "block",
        "reason": f"MemPalace save checkpoint. Write a brief session diary entry covering key topics, decisions, and code changes. Start with:\n\n{summary_escaped}\n\nContinue after saving."
    }

    print(json.dumps(block_json))


def is_verbose_mode() -> bool:
    """Check if verbose mode is enabled"""
    return VERBOSE_MODE


def find_latest_diary(diary_dir: Path) -> Path | None:
    """Find latest diary file

    Args:
        diary_dir: Diary directory path

    Returns:
        Latest diary path or None
    """
    if not diary_dir.exists():
        return None

    files = sorted(
        diary_dir.glob(".session-diary-*.md"),
        key=lambda p: p.name,
        reverse=True
    )

    return files[0] if files else None


def process_summary(diary_dir: Path, session_id: str) -> str:
    """Extract old summary, generate new entry, accumulate with trim

    Args:
        diary_dir: Diary directory
        session_id: Session ID for state storage

    Returns:
        Combined summary
    """
    from .config import STATE_DIR

    # Find latest diary
    latest_diary = find_latest_diary(diary_dir)

    # Extract old summary
    old_summary = ""
    if latest_diary:
        old_summary = extract_summary_section(latest_diary)

    # Generate new entry
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    if latest_diary:
        current_entry = generate_current_entry(latest_diary, timestamp)
    else:
        current_entry = f"### {timestamp} Session Diary\n- **成果：** （待补充）\n- **决策：** （待补充）"

    # Accumulate and trim
    new_summary = accumulate_and_trim_summary(old_summary, current_entry)

    # Save pending summary
    state_dir = STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    pending_file = state_dir / f"{session_id}_pending_summary.txt"
    pending_file.write_text(new_summary)

    return new_summary


def main():
    """Stop hook main entry point

    Input (stdin JSON): {"session_id": "...", "stop_hook_active": false, "transcript_path": "..."}
    Output (stdout JSON): {} or {"decision": "block", "reason": "..."}
    """
    # Read input
    input_data = read_stdin_json()

    session_id = input_data.get('session_id', 'unknown')
    stop_hook_active = input_data.get('stop_hook_active', False)
    transcript_path = Path(input_data.get('transcript_path', ''))

    # Infinite loop prevention: already in save cycle
    if stop_hook_active:
        output_empty()
        return

    # Count exchanges
    if transcript_path.exists():
        exchange_count = count_human_messages(transcript_path)
    else:
        exchange_count = 0

    # Check if time to save
    state = HookState(session_id)
    since_last = exchange_count - state.last_save

    # Log for debugging
    state.log(f"Session {session_id}: {exchange_count} exchanges, {since_last} since last save")

    if since_last >= SAVE_INTERVAL and exchange_count > 0:
        # Update last save point
        state.last_save = exchange_count
        state.save()

        state.log(f"TRIGGERING SAVE at exchange {exchange_count}")

        # Extract and accumulate summary
        summary = process_summary(DIARY_DIR, session_id)

        state.log(f"Generated summary, size: {len(summary.encode('utf-8'))} bytes")

        # Output block decision (or empty for silent mode)
        if is_verbose_mode():
            output_block_with_summary(summary)
        else:
            # Silent mode: return empty JSON
            output_empty()
    else:
        # Not time to save
        output_empty()
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_save_hook.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit save_hook module**

Run:
```bash
git add session_diary/save_hook.py tests/test_save_hook.py
git commit -m "feat(save_hook): add stop hook main logic with summary processing"
```

---

## Task 9: sessionstart_hook.py - SessionStart Hook

**Files:**
- Create: `session_diary/sessionstart_hook.py`
- Create: `tests/test_sessionstart_hook.py`

- [ ] **Step 1: Write failing test for sessionstart_hook**

Create `tests/test_sessionstart_hook.py`:
```python
from pathlib import Path
from session_diary import sessionstart_hook


def test_find_latest_diary_basic():
    """Test finding latest diary"""
    import tempfile

    # Create temp directory with 3 diaries
    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)

        # Create diaries with timestamps in filenames
        Path(diary_dir / ".session-diary-2026-05-01-1000-task1.md").write_text("Diary 1")
        Path(diary_dir / ".session-diary-2026-05-02-1500-task2.md").write_text("Diary 2")
        Path(diary_dir / ".session-diary-2026-05-02-1800-task3.md").write_text("Diary 3")

        latest = sessionstart_hook.find_latest_diary(diary_dir)

        # Should return latest by filename (2026-05-02-1800)
        assert latest is not None
        assert latest.name == ".session-diary-2026-05-02-1800-task3.md"


def test_find_latest_diary_empty_dir():
    """Test finding diary in empty directory"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)

        latest = sessionstart_hook.find_latest_diary(diary_dir)

        assert latest is None


def test_find_latest_diary_nonexistent_dir():
    """Test finding diary when directory doesn't exist"""
    nonexistent = Path("/nonexistent/directory")

    latest = sessionstart_hook.find_latest_diary(nonexistent)

    assert latest is None


def test_output_no_diary_fallback():
    """Test output when no diary exists"""
    import sys
    from io import StringIO

    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        sessionstart_hook.output_no_diary_fallback()
        output = sys.stdout.getvalue()

        assert "SessionStart - Project Memory Injection" in output
        assert "暂无历史会话记录" in output
        assert "注入统计" in output
        assert "Token估算" in output
    finally:
        sys.stdout = old_stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_sessionstart_hook.py::test_find_latest_diary_basic -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'session_diary.sessionstart_hook'"

- [ ] **Step 3: Write sessionstart_hook.py implementation**

Create `session_diary/sessionstart_hook.py`:
```python
"""SessionStart hook - inject project memory into system prompt"""
from pathlib import Path
from .extractor import extract_summary_section
from .config import DIARY_DIR


def find_latest_diary(diary_dir: Path) -> Path | None:
    """Find latest diary file by filename (descending)

    Args:
        diary_dir: Diary directory path

    Returns:
        Latest diary path or None if not found
    """
    if not diary_dir.exists():
        return None

    files = sorted(
        diary_dir.glob(".session-diary-*.md"),
        key=lambda p: p.name,
        reverse=True
    )

    return files[0] if files else None


def extract_recent_progress(diary_path: Path) -> str:
    """Extract recent progress from '## 本次进展' section

    Args:
        diary_path: Diary file path

    Returns:
        First 10 lines of 本次进展 section
    """
    content = diary_path.read_text()

    # Find "## 本次进展" section
    start_idx = content.find("## 本次进展")
    if start_idx == -1:
        return ""

    # Find next ## section (end boundary)
    end_idx = content.find("\n## ", start_idx + len("## 本次进展"))
    if end_idx == -1:
        section_content = content[start_idx:]
    else:
        section_content = content[start_idx:end_idx]

    # Skip header line, take first 10 lines
    lines = section_content.split("\n")[1:11]

    return "\n".join(lines).strip()


def estimate_tokens(text: str) -> str:
    """Estimate token count for text

    Args:
        text: Text to estimate

    Returns:
        Token estimate string like "~800"
    """
    import re

    # Rough estimate: Chinese chars ~1 token each, English ~1 per 4 chars
    chinese_chars = len(re.findall(r'[一-鿿]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    tokens = chinese_chars + english_chars // 4

    return f"~{tokens}"


def output_no_diary_fallback():
    """Output fallback when no diary exists"""
    print("""# SessionStart - Project Memory Injection

## 历史任务摘要

暂无历史会话记录。这是项目的首次会话，或 session-memory 目录为空。

---

## 最近进展

（无）

---

**注入统计：**
- 文件数：0 个
- 摘要大小：0.0 KB
- Token估算：~0 tokens""")


def output_new_format(diary_path: Path, summary_section: str):
    """Output formatted injection for new format diary

    Args:
        diary_path: Diary file path
        summary_section: Extracted summary section
    """
    # Extract recent progress
    recent_progress = extract_recent_progress(diary_path)

    # Calculate size
    total_text = summary_section + recent_progress
    size_kb = len(total_text.encode('utf-8')) / 1024.0
    token_est = estimate_tokens(total_text)

    print(f"""# SessionStart - Project Memory Injection

## 历史任务摘要

{summary_section}

---

## 最近进展（最新 diary）

{recent_progress}

---

**注入统计：**
- 文件数：1 个（最新 diary）
- 摘要大小：{size_kb:.1f} KB
- Token估算：{token_est} tokens""")


def output_old_format(diary_dir: Path):
    """Output backward compatible format for old diaries

    Args:
        diary_dir: Diary directory
    """
    # Read up to 3 latest diaries
    files = sorted(diary_dir.glob(".session-diary-*.md"), reverse=True)[:3]

    entries = []
    total_size = 0

    for diary_path in files:
        content = diary_path.read_text()
        lines = content.split("\n")[1:31]  # skip title, first 30 lines
        entries.append("\n".join(lines))
        total_size += len(content.encode('utf-8'))

    size_kb = total_size / 1024.0
    all_text = "\n".join(entries)
    token_est = estimate_tokens(all_text)

    print(f"""# SessionStart - Project Memory Injection

## 最近会话历史（智能加载+去重）

{format_entries(entries)}

---

**注入统计：**
- 文件数：{len(files)} 个
- 总大小：{size_kb:.1f} KB
- Token估算：{token_est} tokens""")


def format_entries(entries: list) -> str:
    """Format diary entries for output

    Args:
        entries: List of diary content strings

    Returns:
        Formatted output string
    """
    formatted = []
    for idx, entry in enumerate(entries):
        formatted.append(f"### 会话记录 {idx}\n{entry}")

    return "\n\n".join(formatted)


def main():
    """SessionStart hook main entry point

    Outputs formatted memory injection to stdout
    Claude Code injects stdout into system prompt
    """
    diary_dir = DIARY_DIR

    # Find latest diary
    latest_diary = find_latest_diary(diary_dir)

    if not latest_diary:
        output_no_diary_fallback()
        return

    # Check if has summary section
    summary_section = extract_summary_section(latest_diary)

    if summary_section:
        # New format: has summary
        output_new_format(latest_diary, summary_section)
    else:
        # Old format: backward compatible
        output_old_format(diary_dir)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_sessionstart_hook.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit sessionstart_hook module**

Run:
```bash
git add session_diary/sessionstart_hook.py tests/test_sessionstart_hook.py
git commit -m "feat(sessionstart_hook): add session start memory injection"
```

---

## Task 10: installer.py - Auto Configuration Helper

**Files:**
- Create: `session_diary/installer.py`
- Create: `tests/test_installer.py`

- [ ] **Step 1: Write failing test for installer**

Create `tests/test_installer.py`:
```python
from pathlib import Path
from session_diary import installer


def test_find_settings_json_current_dir():
    """Test finding settings.json in current directory"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create .claude/settings.local.json
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        # Change to temp dir
        import os
        old_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            result = installer.find_settings_json()

            assert result is not None
            assert result.name == "settings.local.json"
        finally:
            os.chdir(old_cwd)


def test_find_settings_json_not_found():
    """Test finding settings when it doesn't exist"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        old_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            result = installer.find_settings_json()

            assert result is None
        finally:
            os.chdir(old_cwd)


def test_hooks_already_configured_false():
    """Test checking if hooks configured (not configured)"""
    config = {}

    result = installer.hooks_already_configured(config)

    assert result is False


def test_hooks_already_configured_true():
    """Test checking if hooks configured (already configured)"""
    config = {
        "hooks": {
            "Stop": [{
                "matcher": "*",
                "hooks": [{
                    "type": "command",
                    "command": "session-diary-save-hook",
                    "timeout": 30
                }]
            }]
        }
    }

    result = installer.hooks_already_configured(config)

    assert result is True


def test_add_hooks():
    """Test adding hooks to config"""
    config = {}

    result = installer.add_hooks(config)

    assert "hooks" in result
    assert "Stop" in result["hooks"]
    assert "SessionStart" in result["hooks"]

    # Check Stop hook structure
    stop_hooks = result["hooks"]["Stop"][0]
    assert stop_hooks["matcher"] == "*"
    assert stop_hooks["hooks"][0]["command"] == "session-diary-save-hook"

    # Check SessionStart hook structure
    start_hooks = result["hooks"]["SessionStart"][0]
    assert start_hooks["matcher"] == "*"
    assert start_hooks["hooks"][0]["command"] == "session-diary-sessionstart-hook"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_installer.py::test_find_settings_json_current_dir -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'session_diary.installer'"

- [ ] **Step 3: Write installer.py implementation**

Create `session_diary/installer.py`:
```python
"""Auto-configure Claude Code settings.json"""
import json
from pathlib import Path


def find_settings_json() -> Path | None:
    """Find Claude Code settings file

    Priority: settings.local.json > settings.json

    Returns:
        Settings file path or None
    """
    candidates = [
        Path(".claude/settings.local.json"),
        Path(".claude/settings.json"),
        Path.home() / ".claude/settings.local.json",
        Path.home() / ".claude/settings.json"
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def read_settings(path: Path) -> dict:
    """Read JSON settings file

    Args:
        path: Settings file path

    Returns:
        Config dict or empty dict if invalid
    """
    if not path.exists() or path.stat().st_size == 0:
        return {}

    try:
        content = path.read_text()
        return json.loads(content)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in {path}")
        print("   Please fix or delete the file, then retry")
        return {}


def write_settings(path: Path, config: dict):
    """Write JSON settings file with formatting

    Args:
        path: Settings file path
        config: Config dict
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    content = json.dumps(config, indent=2, ensure_ascii=False)
    path.write_text(content)


def hooks_already_configured(config: dict) -> bool:
    """Check if hooks already configured

    Args:
        config: Config dict

    Returns:
        True if session-diary hooks already configured
    """
    hooks = config.get("hooks", {})

    # Check Stop hook
    stop_hooks = hooks.get("Stop", [])
    for hook_config in stop_hooks:
        for hook in hook_config.get("hooks", []):
            if hook.get("command") == "session-diary-save-hook":
                return True

    # Check SessionStart hook
    start_hooks = hooks.get("SessionStart", [])
    for hook_config in start_hooks:
        for hook in hook_config.get("hooks", []):
            if hook.get("command") == "session-diary-sessionstart-hook":
                return True

    return False


def add_hooks(config: dict) -> dict:
    """Add session diary hooks to config

    Args:
        config: Config dict

    Returns:
        Config with hooks added
    """
    config.setdefault("hooks", {})

    # Add Stop hook
    config["hooks"]["Stop"] = [{
        "matcher": "*",
        "hooks": [{
            "type": "command",
            "command": "session-diary-save-hook",
            "timeout": 30
        }]
    }]

    # Add SessionStart hook
    config["hooks"]["SessionStart"] = [{
        "matcher": "*",
        "hooks": [{
            "type": "command",
            "command": "session-diary-sessionstart-hook",
            "timeout": 10
        }]
    }]

    return config


def main():
    """Auto-configure Claude Code settings.json

    Usage: session-diary-install
    """
    print("🔧 Session Diary Plugin Installer")

    # Find Claude Code config file
    settings_path = find_settings_json()

    if not settings_path:
        print("❌ Claude Code config not found")
        print("   Expected: .claude/settings.local.json or .claude/settings.json")
        print("\n💡 Please create .claude/settings.local.json first:")
        print("   mkdir -p .claude")
        print("   touch .claude/settings.local.json")
        return

    print(f"✅ Found config: {settings_path}")

    # Read existing config
    config = read_settings(settings_path)

    # Check if hooks already configured
    if hooks_already_configured(config):
        print("⚠️  Hooks already configured in settings.json")
        print("   Skipping to avoid duplicate configuration")
        return

    # Add hooks
    config = add_hooks(config)

    # Write back
    write_settings(settings_path, config)

    print("✅ Hooks configured successfully:")
    print("   - Stop hook: session-diary-save-hook")
    print("   - SessionStart hook: session-diary-sessionstart-hook")
    print("\n⚠️  IMPORTANT: Requires Claude Code restart to activate hooks")
    print("   Press Ctrl+C in Claude Code terminal, then restart session")
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_installer.py -v
```

Expected: PASS (5 tests)

- [ ] **Step 5: Commit installer module**

Run:
```bash
git add session_diary/installer.py tests/test_installer.py
git commit -m "feat(installer): add auto-configuration helper for Claude Code"
```

---

## Task 11: __init__.py - Package Metadata

**Files:**
- Create: `session_diary/__init__.py`

- [ ] **Step 1: Write __init__.py with version metadata**

Create `session_diary/__init__.py`:
```python
"""Session Diary Plugin - Lightweight session diary hooks for Claude Code

Zero dependencies, zero vector DB, pure Python hooks.
"""
__version__ = "1.0.0"
__author__ = "Feng Shuai"
__description__ = "Lightweight session diary hooks for Claude Code - zero dependencies"
```

- [ ] **Step 2: Commit __init__.py**

Run:
```bash
git add session_diary/__init__.py
git commit -m "feat(__init__): add package metadata"
```

---

## Task 12: Final Integration and Verification

**Files:**
- Verify all tests pass
- Verify coverage >= 80%

- [ ] **Step 1: Run all tests**

Run:
```bash
pytest tests/ -v --cov=session_diary --cov-report=term-missing
```

Expected: All tests PASS, coverage >= 80%

- [ ] **Step 2: Verify pyproject.toml structure**

Run:
```bash
cat pyproject.toml
```

Expected: Verify console_scripts are correctly configured:
- session-diary-save-hook
- session-diary-sessionstart-hook
- session-diary-install

- [ ] **Step 3: Test uv tool installation locally**

Run:
```bash
# Install locally for testing
uv tool install ./session-diary-plugin

# Verify installation
uv tool list

# Test commands
session-diary-install --help || session-diary-install
```

Expected: Installation successful, commands registered to PATH

- [ ] **Step 4: Create final commit**

Run:
```bash
git add -A
git commit -m "feat: complete session diary plugin implementation

- 7 core modules with TDD workflow
- 30+ tests, 80%+ coverage
- Pure Python (zero external dependencies)
- uv tool installation ready
- Auto-configuration helper
- Backward compatible diary reading
- Summary extraction with 30KB size control
"
```

---

## Self-Review Checklist

After completing all tasks, verify:

**1. Spec Coverage:**
- ✅ config.py - configuration constants (Task 2)
- ✅ counter.py - message counting (Task 3)
- ✅ extractor.py - summary extraction (Tasks 4-6)
- ✅ state.py - hook state management (Task 7)
- ✅ save_hook.py - stop hook (Task 8)
- ✅ sessionstart_hook.py - session start hook (Task 9)
- ✅ installer.py - auto-configuration (Task 10)
- ✅ pyproject.toml - uv tool config (Task 1)
- ✅ README.md - user documentation (Task 1)
- ✅ Zero dependencies (all modules use stdlib only)
- ✅ 80%+ coverage (Task 12)

**2. Placeholder Scan:**
- ✅ No TBD/TODO
- ✅ All functions implemented
- ✅ All tests have actual code
- ✅ No "implement later" or "fill in details"

**3. Type Consistency:**
- ✅ `count_human_messages(Path) -> int` (counter.py, save_hook.py)
- ✅ `extract_summary_section(Path) -> str` (extractor.py, sessionstart_hook.py)
- ✅ `HookState(str)` (state.py, save_hook.py)
- ✅ All file paths use `Path` type
- ✅ All timestamps use `str` "YYYY-MM-DD HH:MM" format

**Plan complete.** All tasks defined with exact code, exact commands, exact expected outputs.