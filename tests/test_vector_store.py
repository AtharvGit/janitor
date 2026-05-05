import pytest
import chromadb
from src.vector_store import ChromaManager

@pytest.fixture
def test_db():
    """Creates a temporary, in-memory database specifically for testing."""
    fake_client = chromadb.EphemeralClient()
    manager = ChromaManager()
    manager.client = chromadb.EphemeralClient()
    
    # FIX: Use get_or_create to prevent "already exists" errors
    manager.collection = manager.client.get_or_create_collection("test_knowledge_base")
    
    # Provide the database to the test
    yield manager
    
    # FIX: Teardown - wipe the collection after the test finishes
    try:
        manager.client.delete_collection("test_knowledge_base")
    except ValueError:
        pass # Ignore if it was already deleted by the test

def test_deduplication_works(test_db):
    """Proves that upserting the same file twice doesn't duplicate chunks."""
    file_path = "dummy/path/report.pdf"
    chunks = ["chunk 1 text", "chunk 2 text"]
    embeddings = [[0.1, 0.2], [0.3, 0.4]]
    
    # Insert first time
    test_db.upsert_document(file_path, chunks, embeddings)
    
    # Insert exactly the same data a second time (Simulating a Modify event)
    test_db.upsert_document(file_path, chunks, embeddings)
    
    # Check the database
    results = test_db.collection.get(where={"file_path": file_path})
    
    # Even though we inserted twice, there should only be 2 chunks total, not 4.
    assert len(results['ids']) == 2

def test_cleanup_on_delete(test_db):
    """Proves that deleting a file purges all its vectors."""
    file_path = "dummy/path/report.pdf"
    chunks = ["chunk 1 text"]
    embeddings = [[0.1, 0.2]]
    
    # Insert the document
    test_db.upsert_document(file_path, chunks, embeddings)
    
    # Verify it exists
    results_before = test_db.collection.get(where={"file_path": file_path})
    assert len(results_before['ids']) == 1
    
    # Trigger the delete protocol
    test_db.delete_document(file_path)
    
    # Verify it is completely gone
    results_after = test_db.collection.get(where={"file_path": file_path})
    assert len(results_after['ids']) == 0