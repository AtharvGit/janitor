import chromadb
from src.logger import get_logger

logger = get_logger('VectorStore')

class ChromaManager:
    def __init__(self, host: str = 'localhost', port: int = 8000):
        try:
            self.client = chromadb.HttpClient(host=host, port=port)
            self.collection = self.client.get_or_create_collection(name='knowledge_base')
            logger.info(f'connected to chromadb at {host}:{port}')
        except Exception as e:
            logger.error(f'failed to connect to chromadb: {e}')
            raise

    def upsert_document(self, file_path: str, chunks:list[str], embededings=list[list[float]]):
        if not chunks:
            return
        
        ids = [f"{file_path}_chunk_{i}" for i in range(len(chunks))] 

        metadatas = [{'file_path':file_path, 'document_type':file_path.split('.')[-1]} for _ in chunks] 

        self.collection.upsert(ids=ids, documents=chunks, embeddings=embededings, metadatas=metadatas)
        logger.info(f'upserted{len(chunks)} chunks for {file_path}')

    def delete_document(self, file_path: str):
        self.collection.delete(where={'file_path': file_path})
        logger.info(f'purged all vectors for deleted file: {file_path}')
        
    