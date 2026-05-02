"""Shared fixtures for session diary tests"""
import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def sample_transcript():
    """Sample JSONL transcript with 6 user messages (excluding 1 command message)"""
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
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def empty_transcript():
    """Empty JSONL transcript"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write("")
        f.flush()
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
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink()


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
        f.flush()
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
        f.flush()
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
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink()
