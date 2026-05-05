import json
import os
from io import StringIO
from pathlib import Path
from session_diary import save_hook


def test_read_stdin_json_invalid():
    import sys
    old_stdin = sys.stdin
    sys.stdin = StringIO("not valid json{{{")
    try:
        result = save_hook.read_stdin_json()
        assert result == {}
    finally:
        sys.stdin = old_stdin


def test_output_block_with_agent_trigger():
    import sys
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        save_hook.output_block_with_agent_trigger(
            Path("/tmp/transcript.json"),
            Path("/tmp/diary_dir")
        )
        output = sys.stdout.getvalue()
        result = json.loads(output)
        assert result["decision"] == "block"
        assert "/save-session-auto" in result["reason"]
        assert "/tmp/transcript.json" in result["reason"]
    finally:
        sys.stdout = old_stdout


def test_find_latest_diary():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)
        Path(diary_dir / ".session-diary-2026-05-01.md").write_text("Old")
        Path(diary_dir / ".session-diary-2026-05-02.md").write_text("New")
        latest = save_hook.find_latest_diary(diary_dir)
        assert latest.name == ".session-diary-2026-05-02.md"


def test_find_latest_diary_nonexistent_dir():
    result = save_hook.find_latest_diary(Path("/nonexistent/dir"))
    assert result is None


def test_find_latest_diary_empty_dir():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        result = save_hook.find_latest_diary(Path(tmpdir))
        assert result is None


def test_process_summary_no_diary():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)
        result = save_hook.process_summary(diary_dir, "test_session")
        assert "## 历史任务摘要" in result
        assert "（待补充）" in result


def test_process_summary_with_diary(sample_diary_new_format):
    diary_dir = sample_diary_new_format.parent
    # Copy the fixture file to a .session-diary-*.md name in the diary dir
    target = diary_dir / ".session-diary-2026-05-02-test.md"
    import shutil
    shutil.copy(str(sample_diary_new_format), str(target))
    try:
        result = save_hook.process_summary(diary_dir, "test_session")
        assert "## 历史任务摘要" in result
        assert "Sample Task" in result
    finally:
        target.unlink()


def test_save_hook_empty_json():
    input_data = {}
    import sys
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    sys.stdin = StringIO(json.dumps(input_data))
    try:
        save_hook.main()
        output = sys.stdout.getvalue()
        result = json.loads(output)
        assert result == {}
    finally:
        sys.stdout = old_stdout


def test_save_hook_stop_hook_active():
    input_data = {
        "session_id": "test_123",
        "stop_hook_active": True,
        "transcript_path": "/tmp/test.jsonl"
    }
    import sys
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    sys.stdin = StringIO(json.dumps(input_data))
    try:
        save_hook.main()
        output = sys.stdout.getvalue()
        result = json.loads(output)
        assert result == {}
    finally:
        sys.stdout = old_stdout


def test_save_hook_missing_transcript():
    input_data = {
        "session_id": "test_456",
        "stop_hook_active": False,
        "transcript_path": "/tmp/nonexistent_transcript_12345.jsonl"
    }
    import sys
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    sys.stdin = StringIO(json.dumps(input_data))
    try:
        save_hook.main()
        output = sys.stdout.getvalue()
        result = json.loads(output)
        assert result == {}
    finally:
        sys.stdout = old_stdout


def test_save_hook_triggers_save(sample_transcript):
    """Cover main() save trigger path: message count + time interval conditions"""
    import sys
    import tempfile
    import importlib
    from session_diary import config, state

    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir) / ".session-memory"
        diary_dir.mkdir()

        # Create state dir in tmpdir to isolate test
        state_dir = Path(tmpdir) / "hook_state"
        state_dir.mkdir()

        input_data = {
            "session_id": "test_save_trigger_fresh",
            "stop_hook_active": False,
            "transcript_path": str(sample_transcript)
        }

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        sys.stdin = StringIO(json.dumps(input_data))

        old_state_dir = os.environ.get('SESSION_DIARY_STATE_DIR')
        os.environ['SESSION_DIARY_STATE_DIR'] = str(state_dir)
        old_diary_dir = os.environ.get('SESSION_DIARY_MEMORY_DIR')
        os.environ['SESSION_DIARY_MEMORY_DIR'] = str(diary_dir)
        old_interval = os.environ.get('SESSION_DIARY_SAVE_INTERVAL')
        os.environ['SESSION_DIARY_SAVE_INTERVAL'] = '1'  # Trigger after 1 message
        old_min_interval = os.environ.get('SESSION_DIARY_MIN_INTERVAL')
        os.environ['SESSION_DIARY_MIN_INTERVAL'] = '0'  # No time restriction for test

        try:
            importlib.reload(config)
            importlib.reload(state)
            importlib.reload(save_hook)
            save_hook.main()
            output = sys.stdout.getvalue()
            result = json.loads(output)
            # Should trigger block with /save-session-auto
            assert result["decision"] == "block"
            assert "/save-session-auto" in result["reason"]
        finally:
            sys.stdout = old_stdout
            if old_state_dir is not None:
                os.environ['SESSION_DIARY_STATE_DIR'] = old_state_dir
            else:
                del os.environ['SESSION_DIARY_STATE_DIR']
            if old_diary_dir is not None:
                os.environ['SESSION_DIARY_MEMORY_DIR'] = old_diary_dir
            else:
                del os.environ['SESSION_DIARY_MEMORY_DIR']
            if old_interval is not None:
                os.environ['SESSION_DIARY_SAVE_INTERVAL'] = old_interval
            else:
                del os.environ['SESSION_DIARY_SAVE_INTERVAL']
            if old_min_interval is not None:
                os.environ['SESSION_DIARY_MIN_INTERVAL'] = old_min_interval
            else:
                del os.environ['SESSION_DIARY_MIN_INTERVAL']
            importlib.reload(config)
            importlib.reload(state)
            importlib.reload(save_hook)


def test_save_hook_time_interval_blocks_save(sample_transcript):
    """Test that time interval condition prevents save"""
    import sys
    import tempfile
    import importlib
    from session_diary import config
    from datetime import datetime

    with tempfile.TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir) / ".session-memory"
        diary_dir.mkdir()

        # Create state file with recent timestamp (5 minutes ago)
        state_dir = Path(tmpdir) / "hook_state"
        state_dir.mkdir()
        recent_time = datetime.now().isoformat()
        state_file = state_dir / "test_time_block_state.json"
        state_file.write_text(json.dumps({
            "last_save_count": 0,
            "last_save_timestamp": recent_time
        }))

        input_data = {
            "session_id": "test_time_block",
            "stop_hook_active": False,
            "transcript_path": str(sample_transcript)
        }

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        sys.stdin = StringIO(json.dumps(input_data))

        old_state_dir = os.environ.get('SESSION_DIARY_STATE_DIR')
        os.environ['SESSION_DIARY_STATE_DIR'] = str(state_dir)
        old_diary_dir = os.environ.get('SESSION_DIARY_MEMORY_DIR')
        os.environ['SESSION_DIARY_MEMORY_DIR'] = str(diary_dir)
        old_interval = os.environ.get('SESSION_DIARY_SAVE_INTERVAL')
        os.environ['SESSION_DIARY_SAVE_INTERVAL'] = '1'
        old_min_interval = os.environ.get('SESSION_DIARY_MIN_INTERVAL')
        os.environ['SESSION_DIARY_MIN_INTERVAL'] = '30'  # 30 minutes required

        try:
            importlib.reload(config)
            importlib.reload(save_hook)
            save_hook.main()
            output = sys.stdout.getvalue()
            result = json.loads(output)
            # Should NOT trigger (time interval not met)
            assert result == {}
        finally:
            sys.stdout = old_stdout
            if old_state_dir is not None:
                os.environ['SESSION_DIARY_STATE_DIR'] = old_state_dir
            else:
                del os.environ['SESSION_DIARY_STATE_DIR']
            if old_diary_dir is not None:
                os.environ['SESSION_DIARY_MEMORY_DIR'] = old_diary_dir
            else:
                del os.environ['SESSION_DIARY_MEMORY_DIR']
            if old_interval is not None:
                os.environ['SESSION_DIARY_SAVE_INTERVAL'] = old_interval
            else:
                del os.environ['SESSION_DIARY_SAVE_INTERVAL']
            if old_min_interval is not None:
                os.environ['SESSION_DIARY_MIN_INTERVAL'] = old_min_interval
            else:
                del os.environ['SESSION_DIARY_MIN_INTERVAL']
            importlib.reload(config)
            importlib.reload(save_hook)
