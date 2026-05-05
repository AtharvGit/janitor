import pytest
import os
from src.processor import DocumentProcessor

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Bypasses the API key requirement so tests can run without hitting the network."""
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_test_key_123")

def test_semantic_chunking_works(mock_env_vars):
    """Proves the recursive text splitter breaks text accurately."""
    processor = DocumentProcessor()
    
    # Create a long text block with clear sentence breaks
    text = "This is the first sentence. " * 50 + "\n\n" + "This is the second paragraph. " * 50
    
    chunks = processor.text_splitter.split_text(text)
    
    # Assertions
    assert len(chunks) > 1  # It should have split the long text
    assert isinstance(chunks, list) # It should return a list
    assert "This is the first sentence." in chunks[0] # The data should be intact