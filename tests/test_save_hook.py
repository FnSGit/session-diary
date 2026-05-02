import json
from io import StringIO
from session_diary import save_hook


def test_save_hook_empty_json():
    """Test save_hook with empty JSON (should output {} and exit)"""
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
    """Test save_hook when stop_hook_active=True (infinite loop prevention)"""
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
    """Test save_hook when transcript_path is missing"""
    input_data = {
        "session_id": "test_456",
        "stop_hook_active": False
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
