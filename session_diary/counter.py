"""Count human messages in JSONL transcript files"""
import json
from pathlib import Path


def count_human_messages(transcript_path: Path) -> int:
    """Count human messages in JSONL transcript

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
