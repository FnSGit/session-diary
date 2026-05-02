"""Extract summary sections from session diaries"""
from pathlib import Path


def extract_summary_section(diary_path: Path) -> str:
    """Extract summary section from diary file

    Args:
        diary_path: Path to .session-diary-*.md file

    Returns:
        Summary section content (from "## 历史任务摘要" to "---")
        Empty string if not found
    """
    # Handle nonexistent file
    if not diary_path.exists():
        return ""

    try:
        content = diary_path.read_text()

        start_marker = "## 历史任务摘要"
        # Only match --- on its own line (markdown horizontal rule)
        end_marker = "\n---\n"

        start_idx = content.find(start_marker)
        if start_idx == -1:
            return ""

        end_idx = content.find(end_marker, start_idx)
        if end_idx == -1:
            # Check if content ends with standalone --- (no trailing newline)
            if content.rstrip().endswith("\n---"):
                end_idx = content.rstrip().rfind("\n---")
            else:
                # No end marker, return rest of file
                return content[start_idx:]

        return content[start_idx:end_idx + len(end_marker)]
    except Exception:
        return ""
