from session_diary.counter import count_human_messages


def test_count_human_messages_basic(sample_transcript):
    """Test counting user messages in basic transcript"""
    result = count_human_messages(sample_transcript)
    # Should count 6 user messages (excluding 1 command message)
    assert result == 6


def test_count_human_messages_empty(empty_transcript):
    """Test counting messages in empty transcript"""
    result = count_human_messages(empty_transcript)
    assert result == 0


def test_count_human_messages_malformed(malformed_transcript):
    """Test counting messages handles malformed JSON gracefully"""
    result = count_human_messages(malformed_transcript)
    # Should count 2 valid user messages, skip malformed line
    assert result == 2


def test_count_human_messages_nonexistent_file():
    """Test counting messages when file doesn't exist"""
    from pathlib import Path
    nonexistent = Path("/nonexistent/file.jsonl")
    result = count_human_messages(nonexistent)
    # Should handle gracefully and return 0
    assert result == 0
