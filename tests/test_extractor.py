from session_diary.extractor import extract_summary_section, generate_current_entry, accumulate_and_trim_summary


def test_extract_summary_section_new_format(sample_diary_new_format):
    """Test extraction from new format diary"""
    result = extract_summary_section(sample_diary_new_format)

    assert "## 历史任务摘要" in result
    assert "### 2026-05-02 18:33 Sample Task" in result
    assert "- **成果：** Test extraction, summary generation" in result
    assert "- **决策：** Use Python instead of bash" in result
    assert "---" in result


def test_extract_summary_section_old_format(sample_diary_old_format):
    """Test extraction from old format diary (should return empty)"""
    result = extract_summary_section(sample_diary_old_format)

    assert result == ""


def test_extract_summary_section_no_end_marker(sample_diary_no_end_marker):
    """Test extraction when no --- end marker exists"""
    result = extract_summary_section(sample_diary_no_end_marker)

    assert "## 历史任务摘要" in result
    assert "### 2026-05-02 20:00 Task Without End" in result
    # Should return rest of file when no end marker
    assert "Content continues without --- separator" in result


def test_extract_summary_section_nonexistent_file():
    """Test extraction when file doesn't exist"""
    from pathlib import Path
    nonexistent = Path("/nonexistent/diary.md")
    result = extract_summary_section(nonexistent)

    assert result == ""


def test_generate_current_entry_basic(sample_diary_new_format):
    """Test basic current entry generation"""
    result = generate_current_entry(sample_diary_new_format, "2026-05-02 20:00")

    assert "### 2026-05-02 20:00" in result
    assert "**成果：**" in result
    assert "**决策：**" in result
    # Should extract task title from first ### in "## 本次进展"
    assert "Sample Task Implementation" in result


def test_generate_current_entry_empty_diary():
    """Test generation when diary is empty"""
    from pathlib import Path
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Empty Diary\n")
        f.flush()
        empty_diary = Path(f.name)

    result = generate_current_entry(empty_diary, "2026-05-02 21:00")

    # Should handle gracefully with placeholders
    assert "### 2026-05-02 21:00" in result
    assert "**成果：** （待补充）" in result
    assert "**决策：** （待补充）" in result

    empty_diary.unlink()


def test_accumulate_and_trim_summary_under_limit():
    """Test accumulation when under 30KB size limit"""
    old_summary = "## 历史任务摘要（截止本次会话）\n\n### Entry 1\n- Item 1\n\n---"
    new_entry = "### 2026-05-02 20:00 New Entry\n- Item new"

    result = accumulate_and_trim_summary(old_summary, new_entry)

    assert "### 2026-05-02 20:00 New Entry" in result
    assert "### Entry 1" in result
    assert "## 历史任务摘要（截止本次会话）" in result
    assert "---" in result


def test_accumulate_and_trim_summary_over_limit():
    """Test trimming when over 30KB limit"""
    # Create large summary (over 30KB)
    entries = []
    for i in range(1, 100):
        pad = "x" * 280
        entries.append(f"### 2026-05-01 {i:02d}:00 Entry {i}\n- Item {i}\n- Detail {i}\n  - {pad}")

    old_summary = "## 历史任务摘要（截止本次会话）\n\n" + "\n\n".join(entries) + "\n\n---"

    # Verify old summary is over 30KB
    assert len(old_summary.encode('utf-8')) > 30720

    new_entry = "### 2026-05-02 20:00 New Entry\n- Item new"
    result = accumulate_and_trim_summary(old_summary, new_entry)

    # Should keep new entry + 5 newest old entries (total 6)
    assert "### 2026-05-02 20:00 New Entry" in result
    assert "### 2026-05-01 99:00 Entry 99" in result  # newest old
    assert "### 2026-05-01 95:00 Entry 95" in result  # 5th newest old
    assert "### 2026-05-01 94:00 Entry 94" not in result  # trimmed

    # Result should be under 30KB
    assert len(result.encode('utf-8')) <= 30720


def test_accumulate_and_trim_summary_empty_old():
    """Test accumulation when old summary is empty"""
    old_summary = ""
    new_entry = "### 2026-05-02 20:00 New Entry\n- Item new"

    result = accumulate_and_trim_summary(old_summary, new_entry)

    assert "### 2026-05-02 20:00 New Entry" in result
    assert "## 历史任务摘要（截止本次会话）" in result
    assert "---" in result
