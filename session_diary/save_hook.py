"""Stop hook main logic - triggers diary saves every N messages"""
import json
import sys
from pathlib import Path
from datetime import datetime
from .counter import count_human_messages
from .extractor import extract_summary_section, generate_current_entry, accumulate_and_trim_summary
from .state import HookState
from .config import SAVE_INTERVAL, DIARY_DIR, VERBOSE_MODE


def read_stdin_json() -> dict:
    """Read JSON input from stdin

    Returns:
        dict with session_id, stop_hook_active, transcript_path
    """
    try:
        input_text = sys.stdin.read()
        return json.loads(input_text)
    except json.JSONDecodeError:
        return {}


def output_empty():
    """Output empty JSON to let AI stop normally"""
    print("{}")


def output_block_with_summary(summary: str):
    """Output block decision with summary

    Args:
        summary: Pending summary to inject
    """
    # Escape newlines for JSON
    summary_escaped = summary.replace("\n", "\\n")

    block_json = {
        "decision": "block",
        "reason": f"MemPalace save checkpoint. Write a brief session diary entry covering key topics, decisions, and code changes. Start with:\n\n{summary_escaped}\n\nContinue after saving."
    }

    print(json.dumps(block_json))


def is_verbose_mode() -> bool:
    """Check if verbose mode is enabled"""
    return VERBOSE_MODE


def find_latest_diary(diary_dir: Path) -> Path | None:
    """Find latest diary file

    Args:
        diary_dir: Diary directory path

    Returns:
        Latest diary path or None
    """
    if not diary_dir.exists():
        return None

    files = sorted(
        diary_dir.glob(".session-diary-*.md"),
        key=lambda p: p.name,
        reverse=True
    )

    return files[0] if files else None


def process_summary(diary_dir: Path, session_id: str) -> str:
    """Extract old summary, generate new entry, accumulate with trim

    Args:
        diary_dir: Diary directory
        session_id: Session ID for state storage

    Returns:
        Combined summary
    """
    from .config import STATE_DIR

    # Find latest diary
    latest_diary = find_latest_diary(diary_dir)

    # Extract old summary
    old_summary = ""
    if latest_diary:
        old_summary = extract_summary_section(latest_diary)

    # Generate new entry
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    if latest_diary:
        current_entry = generate_current_entry(latest_diary, timestamp)
    else:
        current_entry = f"### {timestamp} Session Diary\n- **成果：** （待补充）\n- **决策：** （待补充）"

    # Accumulate and trim
    new_summary = accumulate_and_trim_summary(old_summary, current_entry)

    # Save pending summary
    state_dir = STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    pending_file = state_dir / f"{session_id}_pending_summary.txt"
    pending_file.write_text(new_summary)

    return new_summary


def main():
    """Stop hook main entry point

    Input (stdin JSON): {"session_id": "...", "stop_hook_active": false, "transcript_path": "..."}
    Output (stdout JSON): {} or {"decision": "block", "reason": "..."}
    """
    # Read input
    input_data = read_stdin_json()

    session_id = input_data.get('session_id', 'unknown')
    stop_hook_active = input_data.get('stop_hook_active', False)
    transcript_path = Path(input_data.get('transcript_path', ''))

    # Infinite loop prevention: already in save cycle
    if stop_hook_active:
        output_empty()
        return

    # Count exchanges
    if transcript_path.exists():
        exchange_count = count_human_messages(transcript_path)
    else:
        exchange_count = 0

    # Check if time to save
    state = HookState(session_id)
    since_last = exchange_count - state.last_save

    # Log for debugging
    state.log(f"Session {session_id}: {exchange_count} exchanges, {since_last} since last save")

    if since_last >= SAVE_INTERVAL and exchange_count > 0:
        # Update last save point
        state.last_save = exchange_count
        state.save()

        state.log(f"TRIGGERING SAVE at exchange {exchange_count}")

        # Extract and accumulate summary
        summary = process_summary(DIARY_DIR, session_id)

        state.log(f"Generated summary, size: {len(summary.encode('utf-8'))} bytes")

        # Output block decision (or empty for silent mode)
        if is_verbose_mode():
            output_block_with_summary(summary)
        else:
            # Silent mode: return empty JSON
            output_empty()
    else:
        # Not time to save
        output_empty()
