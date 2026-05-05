import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.logger import get_logger
from src.processor import DocumentProcessor
from src.vector_store import ChromaManager

logger = get_logger("DirectoryWatcher")

class DocumentEventHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        # Initialize the Brain and the Memory
        self.processor = DocumentProcessor()
        self.db = ChromaManager()

    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        logger.info(f"DETECTED CREATE: {file_path}")
        
        # 1. Process the new file
        chunks, embeddings = self.processor.process_file(file_path)
        
        # 2. Store it in the database
        if chunks and embeddings:
            self.db.upsert_document(file_path, chunks, embeddings)

    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path
        logger.info(f"DETECTED MODIFY: {file_path}")
        
        # A modification is essentially a delete and re-create
        self.db.delete_document(file_path)
        chunks, embeddings = self.processor.process_file(file_path)
        
        if chunks and embeddings:
            self.db.upsert_document(file_path, chunks, embeddings)

    def on_deleted(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path
        logger.info(f"DETECTED DELETE: {file_path}")
        
        # Purge the orphaned data
        self.db.delete_document(file_path)

def start_watcher(directory_to_watch: str):
    path = Path(directory_to_watch)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created watch directory: {path.absolute()}")

    event_handler = DocumentEventHandler()
    observer = Observer()
    observer.schedule(event_handler, str(path), recursive=False)
    
    logger.info(f"Starting watcher on directory: {path.absolute()}")
    observer.start()
    
    try:
        while True:
            time.sleep(1) 
    except KeyboardInterrupt:
        logger.info("Watcher interrupted by user. Shutting down gracefully...")
        observer.stop()
    observer.join()