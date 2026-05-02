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
