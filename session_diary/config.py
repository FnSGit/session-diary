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
