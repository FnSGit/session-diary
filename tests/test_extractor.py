from pathlib import Path
from session_diary.extractor import (
    extract_summary_section,
    generate_current_entry,
    accumulate_and_trim_summary,
    extract_first_task_title,
    extract_outcomes,
    extract_decisions,
)


def test_extract_summary_section_new_format(sample_diary_new_format):
    result = extract_summary_section(sample_diary_new_format)
    assert "## 历史任务摘要" in result
    assert "### 2026-05-02 18:33 Sample Task" in result
    assert "- **成果：** Test extraction, summary generation" in result
    assert "- **决策：** Use Python instead of bash" in result
    assert "---" in result


def test_extract_summary_section_old_format(sample_diary_old_format):
    result = extract_summary_section(sample_diary_old_format)
    assert result == ""


def test_extract_summary_section_no_end_marker(sample_diary_no_end_marker):
    result = extract_summary_section(sample_diary_no_end_marker)
    assert "## 历史任务摘要" in result
    assert "### 2026-05-02 20:00 Task Without End" in result
    assert "Content continues without --- separator" in result


def test_extract_summary_section_nonexistent_file():
    nonexistent = Path("/nonexistent/diary.md")
    result = extract_summary_section(nonexistent)
    assert result == ""


def test_extract_summary_section_trailing_separator(sample_diary_trailing_separator):
    """Cover line 34: --- at EOF without trailing newline"""
    result = extract_summary_section(sample_diary_trailing_separator)
    assert "## 历史任务摘要" in result
    assert "### 2026-05-02 20:00 Task" in result
    assert "---" in result


def test_extract_first_task_title_last_section(sample_diary_progress_last_section):
    """Cover line 62: ## 本次进展 is last section"""
    content = sample_diary_progress_last_section.read_text()
    title = extract_first_task_title(content)
    assert title == "My Task Title"


def test_extract_first_task_title_no_header(sample_diary_no_task_title):
    """Cover line 69: no ### header in 本次进展"""
    content = sample_diary_no_task_title.read_text()
    title = extract_first_task_title(content)
    assert title == ""


def test_extract_first_task_title_eof(sample_diary_title_no_trailing_newline):
    """Cover line 75: title with no trailing newline"""
    content = sample_diary_title_no_trailing_newline.read_text()
    title = extract_first_task_title(content)
    assert title == "TitleAtEOF"


def test_extract_outcomes_max_count(sample_diary_many_findings):
    """Cover lines 98+108: outcomes section at end of file, max_count reached"""
    content = sample_diary_many_findings.read_text()
    outcomes = extract_outcomes(content, max_count=5)
    assert outcomes != "（待补充）"
    # Should have exactly 5 findings (max_count=5)
    parts = outcomes.split(", ")
    assert len(parts) == 5
    assert "Finding 1" in outcomes
    assert "Finding 5" in outcomes
    assert "Finding 6" not in outcomes  # truncated by max_count


def test_extract_outcomes_last_section(sample_diary_discoveries_last_section):
    """Cover line 98: ## 关键发现 with no next ## section"""
    content = sample_diary_discoveries_last_section.read_text()
    outcomes = extract_outcomes(content, max_count=5)
    assert "Discovery 1" in outcomes
    assert "Discovery 2" in outcomes


def test_extract_decisions_max_count(sample_diary_many_findings):
    """Cover lines 133+148: decisions section at end of file, max_count reached"""
    content = sample_diary_many_findings.read_text()
    decisions = extract_decisions(content, max_count=3)
    assert decisions != "（待补充）"
    parts = decisions.split(", ")
    assert len(parts) == 3
    assert "Decision One" in decisions
    assert "Decision Three" in decisions
    assert "Decision Four" not in decisions


def test_extract_decisions_last_section(sample_diary_decisions_last_section):
    """Cover line 133: ## 关键决策 with no next ## section"""
    content = sample_diary_decisions_last_section.read_text()
    decisions = extract_decisions(content, max_count=3)
    assert "Important Decision" in decisions


def test_generate_current_entry_basic(sample_diary_new_format):
    result = generate_current_entry(sample_diary_new_format, "2026-05-02 20:00")
    assert "### 2026-05-02 20:00" in result
    assert "**成果：**" in result
    assert "**决策：**" in result
    assert "Sample Task Implementation" in result


def test_generate_current_entry_empty_diary():
    from pathlib import Path
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Empty Diary\n")
        f.flush()
        empty_diary = Path(f.name)

    result = generate_current_entry(empty_diary, "2026-05-02 21:00")
    assert "### 2026-05-02 21:00" in result
    assert "**成果：** （待补充）" in result
    assert "**决策：** （待补充）" in result
    empty_diary.unlink()


def test_generate_current_entry_nonexistent():
    """Cover line 164: diary_path doesn't exist"""
    result = generate_current_entry(Path("/nonexistent/diary.md"), "2026-05-02 22:00")
    assert "### 2026-05-02 22:00 Session Diary" in result
    assert "**成果：** （待补充）" in result
    assert "**决策：** （待补充）" in result


def test_generate_current_entry_no_summary_sections(sample_diary_no_task_title):
    """Cover line 69: no ### header in ## 本次进展"""
    result = generate_current_entry(sample_diary_no_task_title, "2026-05-02 23:00")
    assert "### 2026-05-02 23:00" in result
    # Task title is empty (no ### header), outcomes has "Finding" from 关键发现
    assert "**成果：**" in result
    assert "**决策：**" in result


def test_accumulate_and_trim_summary_under_limit():
    old_summary = "## 历史任务摘要（截止本次会话）\n\n### Entry 1\n- Item 1\n\n---"
    new_entry = "### 2026-05-02 20:00 New Entry\n- Item new"
    result = accumulate_and_trim_summary(old_summary, new_entry)
    assert "### 2026-05-02 20:00 New Entry" in result
    assert "### Entry 1" in result
    assert "## 历史任务摘要（截止本次会话）" in result
    assert "---" in result


def test_accumulate_and_trim_summary_over_limit():
    entries = []
    for i in range(1, 100):
        pad = "x" * 280
        entries.append(f"### 2026-05-01 {i:02d}:00 Entry {i}\n- Item {i}\n- Detail {i}\n  - {pad}")

    old_summary = "## 历史任务摘要（截止本次会话）\n\n" + "\n\n".join(entries) + "\n\n---"
    assert len(old_summary.encode('utf-8')) > 30720

    new_entry = "### 2026-05-02 20:00 New Entry\n- Item new"
    result = accumulate_and_trim_summary(old_summary, new_entry)

    assert "### 2026-05-02 20:00 New Entry" in result
    assert "### 2026-05-01 99:00 Entry 99" in result
    assert "### 2026-05-01 95:00 Entry 95" in result
    assert "### 2026-05-01 94:00 Entry 94" not in result
    assert len(result.encode('utf-8')) <= 30720


def test_accumulate_and_trim_summary_empty_old():
    old_summary = ""
    new_entry = "### 2026-05-02 20:00 New Entry\n- Item new"
    result = accumulate_and_trim_summary(old_summary, new_entry)
    assert "### 2026-05-02 20:00 New Entry" in result
    assert "## 历史任务摘要（截止本次会话）" in result
    assert "---" in result
