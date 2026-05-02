from pathlib import Path
from session_diary import sessionstart_hook


def test_find_latest_diary_basic():
    """Test finding latest diary"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)

        Path(diary_dir / ".session-diary-2026-05-01-1000-task1.md").write_text("Diary 1")
        Path(diary_dir / ".session-diary-2026-05-02-1500-task2.md").write_text("Diary 2")
        Path(diary_dir / ".session-diary-2026-05-02-1800-task3.md").write_text("Diary 3")

        latest = sessionstart_hook.find_latest_diary(diary_dir)

        assert latest is not None
        assert latest.name == ".session-diary-2026-05-02-1800-task3.md"


def test_find_latest_diary_empty_dir():
    """Test finding diary in empty directory"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)
        latest = sessionstart_hook.find_latest_diary(diary_dir)
        assert latest is None


def test_find_latest_diary_nonexistent_dir():
    """Test finding diary when directory doesn't exist"""
    nonexistent = Path("/nonexistent/directory")
    latest = sessionstart_hook.find_latest_diary(nonexistent)
    assert latest is None


def test_output_no_diary_fallback():
    """Test output when no diary exists"""
    import sys
    from io import StringIO

    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        sessionstart_hook.output_no_diary_fallback()
        output = sys.stdout.getvalue()

        assert "SessionStart - Project Memory Injection" in output
        assert "暂无历史会话记录" in output
        assert "注入统计" in output
        assert "Token估算" in output
    finally:
        sys.stdout = old_stdout
