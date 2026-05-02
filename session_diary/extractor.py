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
