"""Stop hook main logic - triggers diary saves every N messages with time interval"""
import json
import sys
from pathlib import Path
from datetime import datetime
from .counter import count_human_messages
from .extractor import extract_summary_section, generate_current_entry, accumulate_and_trim_summary
from .state import HookState, save_diary_dir
from .config import SAVE_INTERVAL, DIARY_DIR, VERBOSE_MODE, MIN_SAVE_INTERVAL_MINUTES


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


def output_block_with_agent_trigger(transcript_path: Path, diary_dir: Path):
    """Output block decision with /save-session-auto trigger

    Args:
        transcript_path: Path to transcript.json
        diary_dir: Path to diary directory
    """
    # Create diary dir if not exists (Agent may need it)
    diary_dir.mkdir(parents=True, exist_ok=True)

    # Format: explicit slash command that Claude will recognize
    trigger_json = {
        "decision": "block",
        "reason": f"请执行 /save-session-auto 启动后台 Agent 总结会话。\n\ntranscript_path={transcript_path}\ndiary_dir={diary_dir}"
    }
    print(json.dumps(trigger_json))


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


def write_diary_file(diary_dir: Path, summary: str) -> Path:
    """Write a diary markdown file to diary_dir

    Args:
        diary_dir: Diary directory (will be created if not exists)
        summary: Summary content to write

    Returns:
        Path to the written diary file
    """
    diary_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    time_short = datetime.now().strftime('%H%M')
    filename = f".session-diary-{timestamp[:10]}-{time_short}.md"
    diary_path = diary_dir / filename

    content = f"# Session Diary - {timestamp}\n\n{summary}\n"
    diary_path.write_text(content, encoding='utf-8')

    return diary_path


def process_summary(diary_dir: Path, session_id: str) -> str:
    """Extract old summary, generate new entry, accumulate with trim, write diary

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

    # Write diary file directly (no AI needed)
    write_diary_file(diary_dir, new_summary)

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

    # Check if time to save (dual conditions: message count + time interval)
    state = HookState(session_id)
    since_last = exchange_count - state.last_save

    # Message count condition
    message_condition = since_last >= SAVE_INTERVAL and exchange_count > 0

    # Time interval condition
    time_condition = True  # Default: allow if no previous timestamp
    if state.last_save_timestamp:
        try:
            last_time = datetime.fromisoformat(state.last_save_timestamp)
            minutes_since_last = (datetime.now() - last_time).total_seconds() / 60
            time_condition = minutes_since_last >= MIN_SAVE_INTERVAL_MINUTES
        except Exception:
            pass  # Invalid timestamp format, allow save

    # Log for debugging
    state.log(f"Session {session_id}: {exchange_count} exchanges, {since_last} since last save")
    state.log(f"Conditions: message={message_condition}, time={time_condition}")

    if message_condition and time_condition:
        # Update last save point and timestamp
        state.last_save = exchange_count
        state.last_save_timestamp = datetime.now().isoformat()
        state.save()

        # Save diary_dir to global state for SessionStart hook
        save_diary_dir(DIARY_DIR)

        state.log(f"TRIGGERING SAVE at exchange {exchange_count}")

        # Output block decision with /save-session-auto trigger
        output_block_with_agent_trigger(transcript_path, DIARY_DIR)
    else:
        # Not time to save
        output_empty()
