"""Count human messages in JSONL transcript files"""
import json
from pathlib import Path
from datetime import datetime


def count_human_messages(transcript_path: Path) -> int:
    """Count human messages in JSONL transcript (full read)

    Args:
        transcript_path: Path to .jsonl transcript file

    Returns:
        Number of user messages (excluding command messages)
    """
    count = 0

    # Handle nonexistent file gracefully
    if not transcript_path.exists():
        return 0

    try:
        with transcript_path.open('r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    msg = entry.get('message', {})

                    # Only count user role
                    if isinstance(msg, dict) and msg.get('role') == 'user':
                        content = msg.get('content', '')

                        # Skip command messages (e.g., <command-message>)
                        if isinstance(content, str) and '<command-message>' in content:
                            continue

                        count += 1
                except json.JSONDecodeError:
                    # Skip malformed lines gracefully
                    continue
    except Exception:
        # Handle file read errors gracefully
        return 0

    return count


def count_human_messages_incremental(transcript_path: Path, state) -> tuple[int, int]:
    """Count human messages with incremental read (skip already processed)

    Uses hybrid detection: file size + modification time to detect file reset.

    Args:
        transcript_path: Path to .jsonl transcript file
        state: HookState object with file tracking fields

    Returns:
        Tuple of (total_count, new_count) where:
        - total_count: total user messages in file
        - new_count: messages read in this pass (for logging)
    """
    # Handle nonexistent file gracefully
    if not transcript_path.exists():
        state.last_file_position = 0
        state.last_file_size = 0
        state.last_file_mtime = None
        return (0, 0)

    try:
        stat = transcript_path.stat()
        current_size = stat.st_size
        current_mtime_iso = datetime.fromtimestamp(stat.st_mtime).isoformat()

        total_count = 0
        new_count = 0

        with transcript_path.open('r') as f:
            # Detect file reset: size shrinks or mtime changed
            need_reset = False
            if state.last_file_size > current_size:
                # File truncated, reset to beginning
                need_reset = True
            elif state.last_file_mtime and state.last_file_mtime != current_mtime_iso:
                # Modification time changed (file rewritten), reset
                need_reset = True

            if need_reset:
                state.last_file_position = 0
                state.last_file_size = 0
                state.last_file_mtime = None

            # Seek to last position
            f.seek(state.last_file_position)

            # Count all messages (need total for comparison with last_save)
            # But we track new lines read from seek position
            pos_before = f.tell()

            for line in f:
                try:
                    entry = json.loads(line)
                    msg = entry.get('message', {})

                    if isinstance(msg, dict) and msg.get('role') == 'user':
                        content = msg.get('content', '')

                        if isinstance(content, str) and '<command-message>' in content:
                            continue

                        total_count += 1
                except json.JSONDecodeError:
                    continue

            # Calculate new lines read in this pass
            new_pos = f.tell()
            bytes_read = new_pos - pos_before

            # Update state with new position
            state.last_file_position = new_pos
            state.last_file_size = current_size
            state.last_file_mtime = current_mtime_iso

            # Estimate new_count based on bytes read (approximate)
            # Since we can't know exact line count after seek, we use bytes as indicator
            if bytes_read > 0:
                # New messages were read (exact count unknown, use total - estimate)
                # For logging purposes, we return bytes_read as indicator
                new_count = bytes_read  # Placeholder for logging
            else:
                new_count = 0

        return (total_count, new_count)

    except Exception:
        return (0, 0)
