import os
from pathlib import Path
from session_diary import sessionstart_hook


def test_find_latest_diary_basic():
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
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)
        latest = sessionstart_hook.find_latest_diary(diary_dir)
        assert latest is None


def test_find_latest_diary_nonexistent_dir():
    nonexistent = Path("/nonexistent/directory")
    latest = sessionstart_hook.find_latest_diary(nonexistent)
    assert latest is None


def test_extract_recent_progress(sample_diary_new_format):
    result = sessionstart_hook.extract_recent_progress(sample_diary_new_format)
    assert "Sample Task Implementation" in result
    assert "Content here..." in result


def test_extract_recent_progress_not_found():
    """Test when ## 本次进展 section doesn't exist"""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Diary without progress section\n\n## Other Section\n\nContent\n")
        f.flush()
        path = Path(f.name)
    result = sessionstart_hook.extract_recent_progress(path)
    path.unlink()
    assert result == ""


def test_estimate_tokens():
    text = "Hello World 你好世界"
    result = sessionstart_hook.estimate_tokens(text)
    assert result.startswith("~")
    tokens = int(result[1:])
    assert tokens > 0


def test_estimate_tokens_chinese_only():
    text = "你好世界测试"
    result = sessionstart_hook.estimate_tokens("你好世界测试")
    assert result.startswith("~")


def test_format_entries():
    entries = ["Content A\nLine 2", "Content B"]
    result = sessionstart_hook.format_entries(entries)
    assert "### 会话记录 0" in result
    assert "Content A" in result
    assert "### 会话记录 1" in result
    assert "Content B" in result


def test_output_no_diary_fallback():
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


def test_output_new_format(sample_diary_new_format):
    import sys
    from io import StringIO
    from session_diary.extractor import extract_summary_section

    summary = extract_summary_section(sample_diary_new_format)
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        sessionstart_hook.output_new_format(sample_diary_new_format, summary)
        output = sys.stdout.getvalue()
        assert "SessionStart - Project Memory Injection" in output
        assert "历史任务摘要" in output
        assert "最近进展" in output
        assert "注入统计" in output
        assert "Sample Task" in output
    finally:
        sys.stdout = old_stdout


def test_output_old_format():
    import sys
    import tempfile
    from io import StringIO

    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)
        Path(diary_dir / ".session-diary-2026-05-01.md").write_text(
            "# Diary 1\n\n## 本次进展\n\nContent 1\n\n## 关键发现\n\n- Finding 1"
        )
        Path(diary_dir / ".session-diary-2026-05-02.md").write_text(
            "# Diary 2\n\n## 本次进展\n\nContent 2\n\n## 关键发现\n\n- Finding 2"
        )

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            sessionstart_hook.output_old_format(diary_dir)
            output = sys.stdout.getvalue()
            assert "SessionStart - Project Memory Injection" in output
            assert "最近会话历史" in output
            assert "注入统计" in output
        finally:
            sys.stdout = old_stdout


def test_main_no_diary():
    import sys
    import tempfile
    from io import StringIO
    from session_diary.state import save_diary_dir

    with tempfile.TemporaryDirectory() as tmpdir:
        # Clear global diary_dir state for test isolation
        save_diary_dir(Path(tmpdir))

        old_diary_dir = os.environ.get('SESSION_DIARY_MEMORY_DIR')
        os.environ['SESSION_DIARY_MEMORY_DIR'] = str(tmpdir)

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            import importlib
            from session_diary import config
            importlib.reload(config)
            importlib.reload(sessionstart_hook)
            sessionstart_hook.main()
            output = sys.stdout.getvalue()
            assert "暂无历史会话记录" in output
        finally:
            sys.stdout = old_stdout
            if old_diary_dir is not None:
                os.environ['SESSION_DIARY_MEMORY_DIR'] = old_diary_dir
            else:
                del os.environ['SESSION_DIARY_MEMORY_DIR']
            importlib.reload(config)
            importlib.reload(sessionstart_hook)


def test_main_with_summary(sample_diary_new_format):
    import sys
    import tempfile
    from io import StringIO
    from session_diary.state import save_diary_dir

    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)
        # Copy fixture as a session diary
        import shutil
        target = diary_dir / ".session-diary-2026-05-02-test.md"
        shutil.copy(str(sample_diary_new_format), str(target))

        # Clear global diary_dir state for test isolation
        save_diary_dir(diary_dir)

        old_diary_dir = os.environ.get('SESSION_DIARY_MEMORY_DIR')
        os.environ['SESSION_DIARY_MEMORY_DIR'] = str(diary_dir)

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            import importlib
            from session_diary import config
            importlib.reload(config)
            importlib.reload(sessionstart_hook)
            sessionstart_hook.main()
            output = sys.stdout.getvalue()
            assert "SessionStart - Project Memory Injection" in output
            assert "Sample Task" in output
        finally:
            sys.stdout = old_stdout
            if old_diary_dir is not None:
                os.environ['SESSION_DIARY_MEMORY_DIR'] = old_diary_dir
            else:
                del os.environ['SESSION_DIARY_MEMORY_DIR']
            importlib.reload(config)
            importlib.reload(sessionstart_hook)


def test_main_with_old_format():
    import sys
    import tempfile
    from io import StringIO
    from session_diary.state import save_diary_dir

    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)
        # Create diary without summary section (old format)
        Path(diary_dir / ".session-diary-2026-05-01-old.md").write_text(
            "# Session Diary\n\n## 本次进展\n\nOld content\n\n## 关键发现\n\n- Finding"
        )

        # Clear global diary_dir state for test isolation
        save_diary_dir(diary_dir)

        old_diary_dir = os.environ.get('SESSION_DIARY_MEMORY_DIR')
        os.environ['SESSION_DIARY_MEMORY_DIR'] = str(diary_dir)

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            import importlib
            from session_diary import config
            importlib.reload(config)
            importlib.reload(sessionstart_hook)
            sessionstart_hook.main()
            output = sys.stdout.getvalue()
            assert "SessionStart - Project Memory Injection" in output
            assert "最近会话历史" in output
        finally:
            sys.stdout = old_stdout
            if old_diary_dir is not None:
                os.environ['SESSION_DIARY_MEMORY_DIR'] = old_diary_dir
            else:
                del os.environ['SESSION_DIARY_MEMORY_DIR']
            importlib.reload(config)
            importlib.reload(sessionstart_hook)
