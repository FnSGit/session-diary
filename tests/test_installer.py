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
        home = Path(tmpdir)

        result = installer.find_settings_json(home_override=home)

        assert result is None


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
