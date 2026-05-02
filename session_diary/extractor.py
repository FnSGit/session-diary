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


def extract_first_task_title(content: str) -> str:
    """Extract first task title from '## 本次进展' section

    Args:
        content: Full diary content

    Returns:
        Task title (first ### header in 本次进展 section)
        Empty string if not found
    """
    # Find "## 本次进展" section
    start_idx = content.find("## 本次进展")
    if start_idx == -1:
        return ""

    # Find next ## section (end boundary)
    end_idx = content.find("\n## ", start_idx + len("## 本次进展"))
    if end_idx == -1:
        section_content = content[start_idx:]
    else:
        section_content = content[start_idx:end_idx]

    # Find first ### header
    title_idx = section_content.find("### ")
    if title_idx == -1:
        return ""

    # Extract title (until newline)
    title_start = title_idx + len("### ")
    title_end = section_content.find("\n", title_start)
    if title_end == -1:
        return section_content[title_start:].strip()

    return section_content[title_start:title_end].strip()


def extract_outcomes(content: str, max_count: int = 5) -> str:
    """Extract outcomes from '## 关键发现' section

    Args:
        content: Full diary content
        max_count: Maximum bullets to extract

    Returns:
        Comma-separated outcomes
    """
    # Find "## 关键发现" section
    start_idx = content.find("## 关键发现")
    if start_idx == -1:
        return "（待补充）"

    # Find next ## section
    end_idx = content.find("\n## ", start_idx + len("## 关键发现"))
    if end_idx == -1:
        section_content = content[start_idx:]
    else:
        section_content = content[start_idx:end_idx]

    # Extract bullet points
    bullets = []
    for line in section_content.split("\n"):
        if line.startswith("- ") and not line.startswith("- **成果") and not line.startswith("- **决策"):
            bullets.append(line[2:].strip())
            if len(bullets) >= max_count:
                break

    return ", ".join(bullets) if bullets else "（待补充）"


def extract_decisions(content: str, max_count: int = 3) -> str:
    """Extract decisions from '## 关键决策' section

    Args:
        content: Full diary content
        max_count: Maximum decisions to extract

    Returns:
        Comma-separated decision titles
    """
    # Find "## 关键决策" section
    start_idx = content.find("## 关键决策")
    if start_idx == -1:
        return "（待补充）"

    # Find next ## section
    end_idx = content.find("\n## ", start_idx + len("## 关键决策"))
    if end_idx == -1:
        section_content = content[start_idx:]
    else:
        section_content = content[start_idx:end_idx]

    # Extract decision titles
    decisions = []
    for line in section_content.split("\n"):
        if line.startswith("**决策") and ":" in line:
            # Extract title between **决策N: title**
            colon_idx = line.find(":")
            if colon_idx != -1:
                title_start = colon_idx + 1
                title_end = line.find("**", title_start)
                if title_end != -1:
                    title = line[title_start:title_end].strip()
                    decisions.append(title)
                    if len(decisions) >= max_count:
                        break

    return ", ".join(decisions) if decisions else "（待补充）"


def generate_current_entry(diary_path: Path, timestamp: str) -> str:
    """Generate current session summary entry

    Args:
        diary_path: Path to current diary
        timestamp: "YYYY-MM-DD HH:MM" format

    Returns:
        Formatted entry: "### YYYY-MM-DD HH:MM Task Title\n- **成果：** ...\n- **决策：** ..."
    """
    if not diary_path.exists():
        return f"### {timestamp} Session Diary\n- **成果：** （待补充）\n- **决策：** （待补充）"

    try:
        content = diary_path.read_text()

        # Extract components
        task_title = extract_first_task_title(content)
        outcomes = extract_outcomes(content, max_count=5)
        decisions = extract_decisions(content, max_count=3)

        # Format entry
        return f"### {timestamp} {task_title}\n- **成果：** {outcomes}\n- **决策：** {decisions}"
    except Exception:
        return f"### {timestamp} Session Diary\n- **成果：** （待补充）\n- **决策：** （待补充）"


def remove_summary_metadata(summary: str) -> str:
    """Remove header and separator from summary

    Args:
        summary: Full summary section

    Returns:
        Content without header line and --- separator
    """
    lines = summary.split("\n")

    # Remove first line (header)
    if lines and lines[0].startswith("## 历史任务摘要"):
        lines = lines[1:]

    # Remove --- separator
    lines = [line for line in lines if line.strip() != "---"]

    return "\n".join(lines).strip()


def extract_summary_entries(summary: str) -> list:
    """Extract individual entries from summary

    Args:
        summary: Full summary section

    Returns:
        List of entry strings (each starts with "### ")
    """
    entries = []
    current_entry = []

    for line in summary.split("\n"):
        if line.startswith("### "):
            if current_entry:
                entries.append("\n".join(current_entry))
            current_entry = [line]
        else:
            if current_entry:
                current_entry.append(line)

    if current_entry:
        entries.append("\n".join(current_entry))

    return entries


def rebuild_summary(entries: list) -> str:
    """Rebuild summary from entries list

    Args:
        entries: List of entry strings

    Returns:
        Full summary section with header and separator
    """
    content = "\n\n".join(entries)
    return f"## 历史任务摘要（截止本次会话）\n\n{content}\n\n---"


def accumulate_and_trim_summary(old_summary: str, new_entry: str) -> str:
    """Accumulate and trim summary entries (size control: 30KB)

    Args:
        old_summary: Full summary section content
        new_entry: New entry to prepend

    Returns:
        Combined summary with size control (max 30KB, trim oldest entries if exceeded)
    """
    from .config import MAX_SUMMARY_SIZE, MAX_SUMMARY_ENTRIES

    # Remove header and separator from old content
    old_content = remove_summary_metadata(old_summary)

    # Build new summary: header + new_entry + old_content + separator
    if old_content:
        new_summary = f"## 历史任务摘要（截止本次会话）\n\n{new_entry}\n\n{old_content}\n\n---"
    else:
        new_summary = f"## 历史任务摘要（截止本次会话）\n\n{new_entry}\n\n---"

    # Check size (30KB = 30720 bytes)
    if len(new_summary.encode('utf-8')) > MAX_SUMMARY_SIZE:
        # Extract entries
        entries = extract_summary_entries(new_summary)

        if len(entries) > MAX_SUMMARY_ENTRIES:
            # Keep new entry (first) + 5 newest old entries (last 5)
            trimmed_entries = [entries[0]] + entries[-(MAX_SUMMARY_ENTRIES - 1):]
            new_summary = rebuild_summary(trimmed_entries)

    return new_summary
