import os
import json
import tempfile
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
    """Test default DIARY_DIR is .session-memory under project root"""
    # DIARY_DIR should be an absolute path ending with .session-memory
    assert config.DIARY_DIR.name == ".session-memory"
    assert config.DIARY_DIR.is_absolute()


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


def test_find_settings_file():
    """Test _find_settings_file finds settings.local.json from CWD upward"""
    import importlib

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / 'test-project'
        project_root.mkdir()

        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        settings_file = claude_dir / 'settings.local.json'
        settings_file.write_text('{}')

        # Change CWD to project root
        old_cwd = os.getcwd()
        os.chdir(project_root)

        # Reload config to pick up new CWD
        importlib.reload(config)

        found = config._find_settings_file()
        assert found == settings_file

        # Cleanup
        os.chdir(old_cwd)


def test_find_settings_file_not_found():
    """Test _find_settings_file returns None when not found"""
    import importlib

    with tempfile.TemporaryDirectory() as tmpdir:
        # Change CWD to temp dir without settings
        old_cwd = os.getcwd()
        os.chdir(tmpdir)

        # Reload config
        importlib.reload(config)

        found = config._find_settings_file()
        assert found is None

        # Cleanup
        os.chdir(old_cwd)


def test_read_settings_local_json():
    """Test _read_settings_local_json parses JSON correctly"""
    import importlib

    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = Path(tmpdir) / 'settings.json'
        settings_file.write_text(json.dumps({'key': 'value'}))

        result = config._read_settings_local_json(settings_file)
        assert result == {'key': 'value'}


def test_read_settings_local_json_invalid():
    """Test _read_settings_local_json returns empty dict for invalid JSON"""
    import importlib

    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = Path(tmpdir) / 'settings.json'
        settings_file.write_text('invalid json')

        result = config._read_settings_local_json(settings_file)
        assert result == {}


def test_get_diary_dir_from_settings():
    """Test _get_diary_dir_from_settings resolves relative path correctly"""
    import importlib

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / 'my-project'
        project_root.mkdir()

        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        settings_file = claude_dir / 'settings.local.json'
        settings_file.write_text(json.dumps({
            'sessionDiary': {'directory': 'custom-memory'}
        }))

        old_cwd = os.getcwd()
        os.chdir(project_root)

        importlib.reload(config)

        diary_dir = config._get_diary_dir_from_settings()
        expected = project_root / 'custom-memory'
        assert diary_dir == expected

        os.chdir(old_cwd)


def test_get_diary_dir_from_settings_simple_format():
    """Test sessionDiaryDirectory simple format"""
    import importlib

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / 'project'
        project_root.mkdir()

        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        settings_file = claude_dir / 'settings.local.json'
        settings_file.write_text(json.dumps({
            'sessionDiaryDirectory': '.diary'
        }))

        old_cwd = os.getcwd()
        os.chdir(project_root)

        importlib.reload(config)

        diary_dir = config._get_diary_dir_from_settings()
        expected = project_root / '.diary'
        assert diary_dir == expected

        os.chdir(old_cwd)


def test_get_diary_dir_from_settings_absolute_path():
    """Test absolute path in settings"""
    import importlib

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / 'project'
        project_root.mkdir()

        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        settings_file = claude_dir / 'settings.local.json'
        # Absolute path should work too
        absolute_path = '/tmp/absolute-diary'
        settings_file.write_text(json.dumps({
            'sessionDiary': {'directory': absolute_path}
        }))

        old_cwd = os.getcwd()
        os.chdir(project_root)

        importlib.reload(config)

        diary_dir = config._get_diary_dir_from_settings()
        # Path('/tmp/project') / '/tmp/absolute-diary' resolves to '/tmp/absolute-diary'
        # because Path handles absolute paths correctly when joining
        assert str(diary_dir) == absolute_path

        os.chdir(old_cwd)
