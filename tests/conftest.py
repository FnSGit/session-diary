"""Shared fixtures for session diary tests"""
import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def sample_transcript():
    """Sample JSONL transcript with 6 user messages (excluding 1 command message)"""
    content = """
{"message": {"role": "user", "content": "Hello"}}
{"message": {"role": "assistant", "content": "Hi"}}
{"message": {"role": "user", "content": "Question 1"}}
{"message": {"role": "assistant", "content": "Answer 1"}}
{"message": {"role": "user", "content": "Question 2"}}
{"message": {"role": "assistant", "content": "Answer 2"}}
{"message": {"role": "user", "content": "<command-message>skip this</command-message>"}}
{"message": {"role": "user", "content": "Question 3"}}
{"message": {"role": "assistant", "content": "Answer 3"}}
{"message": {"role": "user", "content": "Question 4"}}
{"message": {"role": "assistant", "content": "Answer 4"}}
{"message": {"role": "user", "content": "Question 5"}}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(content)
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def empty_transcript():
    """Empty JSONL transcript"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write("")
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def malformed_transcript():
    """JSONL transcript with malformed JSON"""
    content = """
{"message": {"role": "user", "content": "Valid"}}
{invalid json here}
{"message": {"role": "user", "content": "Also valid"}}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(content)
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink()
