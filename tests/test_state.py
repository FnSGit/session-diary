from pathlib import Path
from session_diary.state import HookState


def test_hook_state_init():
    """Test HookState initialization"""
    state = HookState("test_session_123")

    assert state.session_id == "test_session_123"
    assert state.last_save == 0


def test_hook_state_save_and_read():
    """Test saving and reading last_save count"""
    state = HookState("test_session_456")

    state.last_save = 15
    state.save()

    # Create new instance to test reading
    state2 = HookState("test_session_456")
    assert state2.last_save == 15

    # Clean up
    state2.last_save_file.unlink()


def test_hook_state_log():
    """Test logging messages"""
    state = HookState("test_session_789")

    state.log("Test message 1")
    state.log("Test message 2")

    # Verify log file exists and contains messages
    assert state.log_file.exists()

    content = state.log_file.read_text()
    assert "Test message 1" in content
    assert "Test message 2" in content

    # Clean up
    state.log_file.unlink()
    state.state_dir.rmdir()


def test_hook_state_invalid_last_save():
    """Test handling invalid last_save file content"""
    state = HookState("test_session_invalid")

    # Write invalid content
    state.last_save_file.write_text("not_a_number")

    # Create new instance to test validation
    state2 = HookState("test_session_invalid")
    assert state2.last_save == 0  # Should default to 0 for invalid content

    # Clean up
    state2.last_save_file.unlink()
