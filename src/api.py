from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv # <-- ADD THIS

# Load environment variables before doing anything else
load_dotenv() # <-- ADD THIS

from src.vector_store import ChromaManager
from src.processor import DocumentProcessor
from src.logger import get_logger

logger = get_logger("RAG_API")

# Initialize the API
app = FastAPI(
    title="Enterprise RAG API",
    description="Query the automated knowledge base",
    version="1.0.0"
)

# Initialize our brain and memory
db = ChromaManager()
processor = DocumentProcessor()

# Define what the incoming JSON request should look like
class QueryRequest(BaseModel):
    question: str
    num_results: int = 3

@app.post("/query")
async def query_knowledge_base(request: QueryRequest):
    """Takes a user question, vectorizes it, and searches the database."""
    logger.info(f"Received query: {request.question}")
    
    try:
        # 1. Turn the user's text question into a vector using Gemini
        query_embedding = processor.generate_embeddings([request.question])
        
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding.")

        # 2. Search ChromaDB for the closest matching chunks
        results = db.collection.query(
            query_embeddings=query_embedding,
            n_results=request.num_results
        )
        
        # 3. Format the response
        documents = results.get("documents", [[]])[0]
        metadata = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0] # Lower distance = better match
        
        # Combine the data into a clean JSON payload
        matches = []
        for doc, meta, dist in zip(documents, metadata, distances):
            matches.append({
                "text": doc,
                "source_file": meta.get("file_path", "Unknown"),
                "relevance_score": round(1.0 - dist, 4) # Convert distance to a 0-1 score
            })
            
        return {"question": request.question, "matches": matches}

    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))