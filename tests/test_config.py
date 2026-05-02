import os
from pathlib import Path
from session_diary import config


def test_default_save_interval():
    """Test default SAVE_INTERVAL is 15"""
    assert config.SAVE_INTERVAL == 15


def test_default_state_dir():
    """Test default STATE_DIR is ~/.session-diary/hook_state"""
    expected = Path.home() / ".session-diary" / "hook_state"
    assert config.STATE_DIR == expected


def test_default_diary_dir():
    """Test default DIARY_DIR is .session-memory"""
    assert config.DIARY_DIR == Path(".session-memory")


def test_default_verbose_mode():
    """Test default VERBOSE_MODE is False"""
    assert config.VERBOSE_MODE is False


def test_env_override_save_interval():
    """Test SESSION_DIARY_SAVE_INTERVAL env override"""
    os.environ['SESSION_DIARY_SAVE_INTERVAL'] = '10'

    import importlib
    importlib.reload(config)

    assert config.SAVE_INTERVAL == 10

    del os.environ['SESSION_DIARY_SAVE_INTERVAL']


def test_env_override_verbose_mode():
    """Test SESSION_DIARY_VERBOSE env override"""
    os.environ['SESSION_DIARY_VERBOSE'] = 'true'

    import importlib
    importlib.reload(config)

    assert config.VERBOSE_MODE is True

    del os.environ['SESSION_DIARY_VERBOSE']
