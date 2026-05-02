from session_diary.extractor import extract_summary_section


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
