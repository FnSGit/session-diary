import json
import os
from pathlib import Path
from session_diary import installer


def test_find_settings_json_current_dir():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            result = installer.find_settings_json()
            assert result is not None
            assert result.name == "settings.local.json"
        finally:
            os.chdir(old_cwd)


def test_find_settings_json_not_found():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        home = Path(tmpdir)
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            result = installer.find_settings_json(home_override=home)
            assert result is None
        finally:
            os.chdir(old_cwd)


def test_read_settings_valid():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "settings.json"
        path.write_text('{"key": "value"}')
        result = installer.read_settings(path)
        assert result == {"key": "value"}


def test_read_settings_nonexistent():
    result = installer.read_settings(Path("/nonexistent/settings.json"))
    assert result == {}


def test_read_settings_empty_file():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "empty.json"
        path.write_text("")
        result = installer.read_settings(path)
        assert result == {}


def test_read_settings_invalid_json():
    import tempfile
    import sys
    from io import StringIO
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "invalid.json"
        path.write_text("{invalid json")
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            result = installer.read_settings(path)
            assert result == {}
        finally:
            sys.stdout = old_stdout


def test_write_settings():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "new_dir" / "settings.json"
        config = {"hooks": {"Stop": []}}
        installer.write_settings(path, config)
        assert path.exists()
        content = json.loads(path.read_text())
        assert content == config


def test_hooks_already_configured_false():
    assert installer.hooks_already_configured({}) is False


def test_hooks_already_configured_true():
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
    assert installer.hooks_already_configured(config) is True


def test_hooks_already_configured_sessionstart():
    config = {
        "hooks": {
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
    assert installer.hooks_already_configured(config) is True


def test_add_hooks():
    config = {}
    result = installer.add_hooks(config)
    assert "hooks" in result
    assert "Stop" in result["hooks"]
    assert "SessionStart" in result["hooks"]
    stop_hooks = result["hooks"]["Stop"][0]
    assert stop_hooks["matcher"] == "*"
    assert stop_hooks["hooks"][0]["command"] == "session-diary-save-hook"
    start_hooks = result["hooks"]["SessionStart"][0]
    assert start_hooks["matcher"] == "*"
    assert start_hooks["hooks"][0]["command"] == "session-diary-sessionstart-hook"


def test_main_with_empty_config():
    import sys
    import tempfile
    from io import StringIO

    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.local.json"
        settings.write_text("{}")

        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            installer.main()
            output = sys.stdout.getvalue()
            assert "configured successfully" in output
            content = json.loads(settings.read_text())
            assert "hooks" in content
        finally:
            sys.stdout = old_stdout
            os.chdir(old_cwd)


def test_main_hooks_already_there():
    import sys
    import tempfile
    from io import StringIO

    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.local.json"
        settings.write_text(json.dumps({
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
        }))

        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            installer.main()
            output = sys.stdout.getvalue()
            assert "already configured" in output
        finally:
            sys.stdout = old_stdout
            os.chdir(old_cwd)
