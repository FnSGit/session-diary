"""Manage hook state for sessions"""
import json
from datetime import datetime
from pathlib import Path
from .config import STATE_DIR


# Global diary directory record file
LAST_DIARY_DIR_FILE = STATE_DIR / "last_diary_dir.txt"


def save_diary_dir(diary_dir: Path):
    """Save diary directory to global state file

    Args:
        diary_dir: Path to diary directory
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LAST_DIARY_DIR_FILE.write_text(str(diary_dir))


def load_diary_dir() -> Path | None:
    """Load diary directory from global state file

    Returns:
        Last used diary directory, or None if not found
    """
    if not LAST_DIARY_DIR_FILE.exists():
        return None
    try:
        return Path(LAST_DIARY_DIR_FILE.read_text().strip())
    except Exception:
        return None


class HookState:
    """Manage hook state for a session

    State directory: ~/.session-diary/hook_state/
    State file: {session_id}_state.json (new format) or {session_id}_last_save.txt (legacy)
    Log file: hook.log
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state_dir = STATE_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # New JSON format file
        self.state_file = self.state_dir / f"{session_id}_state.json"
        # Legacy file (for backward compatibility)
        self.legacy_file = self.state_dir / f"{session_id}_last_save.txt"
        self.log_file = self.state_dir / "hook.log"

        # Load state (with backward compatibility)
        state = self._read_state()
        self.last_save = state.get("last_save_count", 0)
        self.last_save_timestamp = state.get("last_save_timestamp")

    def _read_state(self) -> dict:
        """Read state from JSON file, with legacy format fallback"""
        # Try new JSON format first
        if self.state_file.exists():
            try:
                content = self.state_file.read_text()
                return json.loads(content)
            except (json.JSONDecodeError, Exception):
                pass

        # Fallback: legacy format (pure number)
        if self.legacy_file.exists():
            try:
                content = self.legacy_file.read_text().strip()
                if content.isdigit():
                    return {
                        "last_save_count": int(content),
                        "last_save_timestamp": None  # Unknown timestamp
                    }
            except Exception:
                pass

        return {"last_save_count": 0, "last_save_timestamp": None}

    def save(self):
        """Save current state to JSON file"""
        state = {
            "last_save_count": self.last_save,
            "last_save_timestamp": self.last_save_timestamp or datetime.now().isoformat()
        }
        self.state_file.write_text(json.dumps(state, indent=2))

        # Clean up legacy file if exists
        if self.legacy_file.exists():
            self.legacy_file.unlink()

    def log(self, message: str):
        """Append log message to hook.log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"

        # Append to log file
        with self.log_file.open('a') as f:
            f.write(log_entry)
