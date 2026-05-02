"""SessionStart hook - inject project memory into system prompt"""
from pathlib import Path
from .extractor import extract_summary_section
from .config import DIARY_DIR


def find_latest_diary(diary_dir: Path) -> Path | None:
    """Find latest diary file by filename (descending)

    Args:
        diary_dir: Diary directory path

    Returns:
        Latest diary path or None if not found
    """
    if not diary_dir.exists():
        return None

    files = sorted(
        diary_dir.glob(".session-diary-*.md"),
        key=lambda p: p.name,
        reverse=True
    )

    return files[0] if files else None


def extract_recent_progress(diary_path: Path) -> str:
    """Extract recent progress from '## 本次进展' section

    Args:
        diary_path: Diary file path

    Returns:
        First 10 lines of 本次进展 section
    """
    content = diary_path.read_text()

    start_idx = content.find("## 本次进展")
    if start_idx == -1:
        return ""

    end_idx = content.find("\n## ", start_idx + len("## 本次进展"))
    if end_idx == -1:
        section_content = content[start_idx:]
    else:
        section_content = content[start_idx:end_idx]

    lines = section_content.split("\n")[1:11]

    return "\n".join(lines).strip()


def estimate_tokens(text: str) -> str:
    """Estimate token count for text

    Args:
        text: Text to estimate

    Returns:
        Token estimate string like "~800"
    """
    import re

    chinese_chars = len(re.findall(r'[一-鿿]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    tokens = chinese_chars + english_chars // 4

    return f"~{tokens}"


def output_no_diary_fallback():
    """Output fallback when no diary exists"""
    print("""# SessionStart - Project Memory Injection

## 历史任务摘要

暂无历史会话记录。这是项目的首次会话，或 session-memory 目录为空。

---

## 最近进展

（无）

---

**注入统计：**
- 文件数：0 个
- 摘要大小：0.0 KB
- Token估算：~0 tokens""")


def output_new_format(diary_path: Path, summary_section: str):
    """Output formatted injection for new format diary"""
    recent_progress = extract_recent_progress(diary_path)

    total_text = summary_section + recent_progress
    size_kb = len(total_text.encode('utf-8')) / 1024.0
    token_est = estimate_tokens(total_text)

    print(f"""# SessionStart - Project Memory Injection

## 历史任务摘要

{summary_section}

---

## 最近进展（最新 diary）

{recent_progress}

---

**注入统计：**
- 文件数：1 个（最新 diary）
- 摘要大小：{size_kb:.1f} KB
- Token估算：{token_est} tokens""")


def output_old_format(diary_dir: Path):
    """Output backward compatible format for old diaries"""
    files = sorted(diary_dir.glob(".session-diary-*.md"), reverse=True)[:3]

    entries = []
    total_size = 0

    for diary_path in files:
        content = diary_path.read_text()
        lines = content.split("\n")[1:31]
        entries.append("\n".join(lines))
        total_size += len(content.encode('utf-8'))

    size_kb = total_size / 1024.0
    all_text = "\n".join(entries)
    token_est = estimate_tokens(all_text)

    print(f"""# SessionStart - Project Memory Injection

## 最近会话历史（智能加载+去重）

{format_entries(entries)}

---

**注入统计：**
- 文件数：{len(files)} 个
- 总大小：{size_kb:.1f} KB
- Token估算：{token_est} tokens""")


def format_entries(entries: list) -> str:
    """Format diary entries for output"""
    formatted = []
    for idx, entry in enumerate(entries):
        formatted.append(f"### 会话记录 {idx}\n{entry}")

    return "\n\n".join(formatted)


def main():
    """SessionStart hook main entry point"""
    diary_dir = DIARY_DIR

    latest_diary = find_latest_diary(diary_dir)

    if not latest_diary:
        output_no_diary_fallback()
        return

    summary_section = extract_summary_section(latest_diary)

    if summary_section:
        output_new_format(latest_diary, summary_section)
    else:
        output_old_format(diary_dir)
