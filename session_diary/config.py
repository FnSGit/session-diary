"""Configuration constants for session diary plugin

All constants can be overridden via environment variables.
"""
from pathlib import Path
import os
import json


def _find_settings_file() -> Path | None:
    """Find .claude/settings.local.json from CWD upward

    Returns:
        Path to settings.local.json if found, or None
    """
    cwd = Path.cwd()
    for candidate in [cwd] + list(cwd.parents):
        settings_file = candidate / '.claude' / 'settings.local.json'
        if settings_file.exists():
            return settings_file
    return None


def _read_settings_local_json(settings_file: Path) -> dict:
    """Read settings.local.json file

    Args:
        settings_file: Path to settings.local.json

    Returns:
        Settings dict, or empty dict if not found/invalid
    """
    if not settings_file.exists():
        return {}

    try:
        content = settings_file.read_text()
        return json.loads(content)
    except (json.JSONDecodeError, Exception):
        return {}


def _get_diary_dir_from_settings() -> Path | None:
    """Get diary directory from settings.local.json

    Uses .claude/settings.local.json location to determine project root.
    The .claude directory's parent is the reliable project root.

    Returns:
        Diary directory path if configured, or None
    """
    settings_file = _find_settings_file()
    if not settings_file:
        return None

    # .claude's parent is the project root
    project_root = settings_file.parent.parent

    settings = _read_settings_local_json(settings_file)
    # Support two formats:
    # 1. {"sessionDiary": {"directory": ".session-memory"}}
    # 2. {"sessionDiaryDirectory": ".session-memory"}
    if 'sessionDiary' in settings:
        directory = settings['sessionDiary'].get('directory')
        if directory:
            return project_root / directory
    elif 'sessionDiaryDirectory' in settings:
        directory = settings['sessionDiaryDirectory']
        if directory:
            return project_root / directory
    return None


def _decode_wrapper_path(wrapper_name: str) -> Path | None:
    """Decode Claude Code wrapper directory name to actual project path

    Claude Code encodes paths by replacing '/' with '-', but directory names
    containing '-' are also preserved, making decoding ambiguous.

    Strategy: Try all possible combinations of '-' as '/' or preserving '-',
    and validate which one exists.

    Args:
        wrapper_name: Directory name like '-home-fengshuai-projects-python-projects-novel-agent'

    Returns:
        Decoded Path if found, or None
    """
    # Remove leading '-'
    escaped = wrapper_name.lstrip('-')
    parts = escaped.split('-')

    def generate_candidates(parts_list: list, current_path: Path = Path('/')) -> list:
        """Generate all possible path combinations recursively"""
        if not parts_list:
            return [current_path]

        results = []
        # Try combining 1 to remaining parts as a single segment
        for i in range(1, len(parts_list) + 1):
            # Combine first i parts with '-' (preserving dash)
            combined = '-'.join(parts_list[:i])
            new_path = current_path / combined

            # Recursively process remaining parts
            remaining = parts_list[i:]
            results.extend(generate_candidates(remaining, new_path))

        return results

    candidates = generate_candidates(parts)

    # Validate candidates - prefer ones with project markers
    for candidate in candidates:
        if candidate.exists():
            # Check for project markers
            has_marker = False
            for marker in ['.git', 'pyproject.toml', 'package.json', 'Cargo.toml', 'go.mod', 'Makefile', 'CLAUDE.md']:
                if (candidate / marker).exists():
                    has_marker = True
                    break
            if has_marker:
                return candidate

    # Return first existing candidate even without marker
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def _find_project_root() -> Path:
    """Find the project root directory

    Uses multiple strategies to locate the actual project root,
    especially when running from Claude Code's wrapper directory.
    """
    cwd = Path.cwd()

    # Strategy 1: Decode Claude Code's wrapper directory pattern
    # Pattern: ~/.claude/projects/-home-fengshuai-projects-MyProject/
    if (cwd.parts[-1].startswith('-') and
            len(cwd.parts) >= 3 and
            cwd.parts[-3] == '.claude' and
            cwd.parts[-2] == 'projects'):
        # Try multiple decodings and validate
        decoded = _decode_wrapper_path(cwd.parts[-1])
        if decoded:
            return decoded

    # Strategy 2: Look for .git first (most reliable project root marker)
    for candidate in [cwd] + list(cwd.parents):
        if (candidate / '.git').exists():
            return candidate

    # Strategy 3: Look for other project markers upward from CWD
    markers = ['pyproject.toml', 'package.json', 'Cargo.toml', 'go.mod', 'Makefile', 'CLAUDE.md']
    for candidate in [cwd] + list(cwd.parents):
        for marker in markers:
            if (candidate / marker).exists():
                return candidate

    # Fallback: current directory
    return cwd


# Save interval: every N human messages (default: 30, reduced frequency)
SAVE_INTERVAL = int(os.getenv('SESSION_DIARY_SAVE_INTERVAL', '30'))

# Minimum time interval between saves (minutes, default: 60)
MIN_SAVE_INTERVAL_MINUTES = int(os.getenv('SESSION_DIARY_MIN_INTERVAL', '60'))

# State directory (hook state files, logs)
STATE_DIR = Path(os.getenv('SESSION_DIARY_STATE_DIR', '~/.session-diary/hook_state')).expanduser()

# Diary directory (session diary markdown files)
# Automatically finds project root, or uses SESSION_DIARY_MEMORY_DIR if set
_DIARY_DIR_NAME = os.getenv('SESSION_DIARY_MEMORY_DIR')
if _DIARY_DIR_NAME:
    DIARY_DIR = Path(_DIARY_DIR_NAME)
else:
    # Priority 1: settings.local.json configuration (most reliable)
    _settings_diary_dir = _get_diary_dir_from_settings()
    if _settings_diary_dir:
        DIARY_DIR = _settings_diary_dir
    else:
        # Priority 2: wrapper decode + project markers
        _project_root = _find_project_root()
        DIARY_DIR = _project_root / '.session-memory'

# Verbose mode: block and show diaries in chat (true) or silent mode (false)
VERBOSE_MODE = os.getenv('SESSION_DIARY_VERBOSE', 'false').lower() in ('true', '1', 'yes')

# Size limit for summary section (30KB)
MAX_SUMMARY_SIZE = 30720  # bytes

# Max entries to keep when trimming
MAX_SUMMARY_ENTRIES = 6  # new entry + 5 newest old entries
