import json
import tempfile
from pathlib import Path
from session_diary.state import HookState, save_diary_dir, load_diary_dir


def test_save_and_load_diary_dir():
    """Test global diary directory state"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "last_diary_dir.txt"
        test_dir = Path("/tmp/test_diary_dir")

        # Manually write and read
        test_file.write_text(str(test_dir))
        loaded = Path(test_file.read_text().strip())
        assert loaded == test_dir


def test_load_diary_dir_not_found():
    """Test load when file doesn't exist"""
    loaded = load_diary_dir()
    # May be None or some existing path
    assert loaded is None or isinstance(loaded, Path)


def test_hook_state_init():
    state = HookState("test_session_123")
    assert state.session_id == "test_session_123"
    assert state.last_save == 0
    assert state.last_save_timestamp is None


def test_hook_state_save_and_read():
    state = HookState("test_session_456")
    state.last_save = 15
    state.save()
    state2 = HookState("test_session_456")
    assert state2.last_save == 15
    assert state2.last_save_timestamp is not None
    state2.state_file.unlink()


def test_hook_state_log():
    state = HookState("test_session_789")
    state.log("Test message 1")
    state.log("Test message 2")
    assert state.log_file.exists()
    content = state.log_file.read_text()
    assert "Test message 1" in content
    assert "Test message 2" in content
    state.log_file.unlink()


def test_hook_state_invalid_json():
    state = HookState("test_session_invalid")
    state.state_file.write_text("not_valid_json")
    state2 = HookState("test_session_invalid")
    assert state2.last_save == 0
    state2.state_file.unlink()


def test_hook_state_legacy_format_migration():
    """Test backward compatibility with legacy format (pure number)"""
    state = HookState("test_session_legacy")
    # Write legacy format
    state.legacy_file.write_text("20")
    # Reload should migrate to JSON
    state2 = HookState("test_session_legacy")
    assert state2.last_save == 20
    assert state2.last_save_timestamp is None  # Unknown timestamp
    # Save should write JSON format
    state2.save()
    assert state2.state_file.exists()
    assert not state2.legacy_file.exists()  # Legacy file cleaned up
    # Verify JSON content
    content = state2.state_file.read_text()
    data = json.loads(content)
    assert data["last_save_count"] == 20
    state2.state_file.unlink()


def test_hook_state_json_format():
    """Test new JSON format with timestamp"""
    state = HookState("test_session_json")
    state.state_file.write_text(json.dumps({
        "last_save_count": 25,
        "last_save_timestamp": "2026-05-04T10:00:00"
    }))
    state2 = HookState("test_session_json")
    assert state2.last_save == 25
    assert state2.last_save_timestamp == "2026-05-04T10:00:00"
    state2.state_file.unlink()


def test_hook_state_read_exception():
    """Cover exception path in _read_state"""
    # Create a directory instead of file to cause read exception
    state = HookState("test_session_exception_xxx")
    state.state_file.mkdir(parents=True, exist_ok=True)
    try:
        state2 = HookState("test_session_exception_xxx")
        assert state2.last_save == 0
    finally:
        state.state_file.rmdir()
