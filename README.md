# Session Diary Plugin

> Lightweight session diary hooks for Claude Code - zero dependencies, zero vector DB

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-89%25-green.svg)](tests/)

**English** | [中文文档](README_CN.md)

## Why This Exists

**Problem:** MemPalace consumes heavy resources (Qdrant vector DB + GPU), WSL GPU virtualization causes crashes.

**Solution:** Extract session diary functionality into a lightweight package - only hooks + markdown storage, zero heavy dependencies.

## Features

- ✅ **Zero Dependencies** - Pure Python standard library (no third-party packages)
- ✅ **Zero Resource Usage** - No vector DB, no GPU, no background processes
- ✅ **Fast Install** - `uv tool install session-diary-plugin`
- ✅ **Auto Config** - `session-diary-install` one-click hook setup
- ✅ **Backward Compatible** - Auto-reads both new and old diary formats
- ✅ **Incremental Summary** - 30KB size limit, auto-trims old entries
- ✅ **Smart Throttling** - Dual trigger conditions (message count + time interval)
- ✅ **Custom Config** - settings.local.json support for diary directory

## Architecture

```
Claude Code Hook Mechanism
    ├── Stop Hook (triggered at session end)
    │   └── Dual conditions: N messages + time interval
    │       ├── Count messages
    │       ├── Extract history summary
    │       ├── Generate current entry
    │       ├── Accumulate & trim (30KB limit)
    │       └── Write Markdown diary file
    │
    └── SessionStart Hook (triggered at new session)
        └── Read latest diary file
            ├── Extract historical task summary
            ├── Extract recent progress
            └── Inject into system prompt
```

## Installation

```bash
# 1. Install via uv tool
uv tool install session-diary-plugin

# 2. Verify installation
uv tool list
# Expected output:
# session-diary-plugin v1.0.0
# - session-diary-install
# - session-diary-save-hook
# - session-diary-sessionstart-hook

# 3. Configure Claude Code
session-diary-install

# 4. Restart Claude Code
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_DIARY_SAVE_INTERVAL` | `15` | Save interval (message count) |
| `SESSION_DIARY_MIN_INTERVAL` | `30` | Minimum time interval (minutes) |
| `SESSION_DIARY_VERBOSE` | `false` | Verbose mode (show in chat) |
| `SESSION_DIARY_MEMORY_DIR` | `.session-memory` | Diary directory name |
| `SESSION_DIARY_STATE_DIR` | `~/.session-diary/hook_state` | State directory |

### settings.local.json

Custom diary directory per project:

```json
// .claude/settings.local.json
{
  "sessionDiary": {
    "directory": ".session-memory"
  }
}
```

Or simplified format:

```json
{
  "sessionDiaryDirectory": ".session-memory"
}
```

**Priority**: Environment variable > settings.local.json > wrapper decode > default

### Diary File Format

Generated files: `.session-diary-YYYY-MM-DD-HHMM-topic.md`

```markdown
# Session Diary - YYYY-MM-DD HH:MM

## Historical Task Summary

### YYYY-MM-DD HH:MM Task Title
- **Outcome:** Key achievements
- **Decision:** Important decisions

---

## Current Progress

### Task Title
- Specific progress
- Code changes summary
- Problem solving process

## Key Findings

- Finding 1
- Finding 2

## Key Decisions

**Decision 1: Choice and reason**
- Reason explanation
```

## Development

### Setup Dev Environment

```bash
# Clone repository
git clone git@github.com:FnSGit/session-diary.git
cd session-diary

# Create virtual environment (Python 3.14)
uv venv --python 3.14
source .venv/bin/activate  # Linux/macOS

# Install dev dependencies
uv pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=session_diary --cov-report=term-missing

# Coverage requirement: >= 80%
```

### Test Hooks Locally

```bash
# Test Stop Hook
echo '{"session_id":"test","stop_hook_active":false,"transcript_path":"/tmp/test.jsonl"}' | session-diary-save-hook

# Test SessionStart Hook
session-diary-sessionstart-hook

# Test Installer
session-diary-install --dry-run
```

## Module Structure

| Module | Purpose | Entry Point |
|--------|---------|-------------|
| `save_hook.py` | Stop Hook main logic | `main()` |
| `sessionstart_hook.py` | SessionStart Hook logic | `main()` |
| `installer.py` | Auto-configuration tool | `main()` |
| `extractor.py` | Summary extraction | Helper functions |
| `config.py` | Configuration & path resolution | Constants |
| `state.py` | Hook state persistence | `HookState` class |
| `counter.py` | Message counting | `count_exchanges()` |

## FAQ

**Q: Hook not triggering?**
- Check `~/.claude/settings.json` configuration
- Confirm Claude Code restarted
- Check logs: `~/.session-diary/hook_state/hook.log`

**Q: Where are diary files?**
- Default: `.session-memory/` in project root
- Customizable via environment variable or settings.local.json

**Q: How to debug?**
- Set `SESSION_DIARY_VERBOSE=true`
- Check hook.log
- Run tests with pytest

**Q: How to customize diary directory?**
- Add `sessionDiary.directory` to `.claude/settings.local.json`
- Path resolved relative to `.claude` parent directory

## License

MIT License - see [LICENSE](LICENSE) file.

## Changelog

### 2026-05-05
- Added settings.local.json configuration support
- Improved wrapper directory name decoding (recursive algorithm)
- Test coverage: 84 tests, 89.47%

### 2026-05-03
- Initial release
- Complete hook implementation
- Auto-configuration installer
- 73 tests, 94.58% coverage