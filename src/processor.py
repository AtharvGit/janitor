import os
from google import genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tenacity import retry, wait_exponential, stop_after_attempt
from src.logger import get_logger

logger = get_logger('DocumentProcessor')

class DocumentProcessor:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error('API Key missing from environment')
            raise ValueError('API key required')
        
        self.client = genai.Client(api_key=api_key)

        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200, separators=["\n\n", "\n", ".", " ", ""])

    def extract_text(self, file_path:str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f'failed to read {file_path}:{e}')
            return ""
        
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(5))
    def generate_embeddings(self, chunks: list[str]) ->list[list[float]]:
        if not chunks:
            return []
        logger.info(f'generate embedding for {len(chunks)} chunks')

        result = self.client.models.embed_content(model='gemini-embedding-001', contents=chunks)
        return [embedding.values for embedding in result.embeddings]
    
    def process_file(self, file_path: str) ->tuple[list[str], list[list[float]]]:
        text = self.extract_text(file_path)
        if not text:
            return [], []
        
        chunks = self.text_splitter.split_text(text)
        embeddings = self.generate_embeddings(chunks)

        return chunks, embeddings
