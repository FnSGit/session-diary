"""Auto-configure Claude Code settings.json"""
import json
from pathlib import Path


def find_settings_json(home_override: Path | None = None) -> Path | None:
    """Find Claude Code settings file

    Priority: settings.local.json > settings.json

    Args:
        home_override: Optional home directory override (for testing)

    Returns:
        Settings file path or None
    """
    home = home_override if home_override is not None else Path.home()

    candidates = [
        Path(".claude/settings.local.json"),
        Path(".claude/settings.json"),
        home / ".claude/settings.local.json",
        home / ".claude/settings.json"
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
