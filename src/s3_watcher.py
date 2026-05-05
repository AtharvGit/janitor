import time
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv # <-- ADD THIS

# Load environment variables before starting the watcher
load_dotenv() # <-- ADD THIS

from src.logger import get_logger
from src.processor import DocumentProcessor
from src.vector_store import ChromaManager
from pathlib import Path

logger = get_logger("S3CloudWatcher")

class S3Watcher:
    def __init__(self, bucket_name: str, endpoint_url: str = "http://localhost:4566"):
        self.bucket_name = bucket_name
        
        # Connect to the local AWS emulator using dummy credentials
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="eu-central-1"
        )
        self.processor = DocumentProcessor()
        self.db = ChromaManager()
        self.state = {} # Memory of the bucket: maps 'filename' -> 'ETag'
        
        # Ensure our temporary download folder exists
        Path("./data").mkdir(exist_ok=True)
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Connected to existing S3 Bucket: {self.bucket_name}")
        except ClientError:
            logger.info(f"Provisioning new S3 Bucket: {self.bucket_name}")
            self.s3.create_bucket(
                Bucket=self.bucket_name,
                CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'}
            )

    def _download_file(self, key: str) -> str:
        """Downloads the cloud file to our local worker for processing."""
        local_path = f"./data/{key.replace('/', '_')}"
        self.s3.download_file(self.bucket_name, key, local_path)
        return local_path

    def poll(self):
        logger.info(f"Starting cloud polling loop on s3://{self.bucket_name} ...")
        try:
            while True:
                response = self.s3.list_objects_v2(Bucket=self.bucket_name)
                current_objects = response.get('Contents', [])
                current_state = {obj['Key']: obj['ETag'] for obj in current_objects}

                # 1. Detect Creates and Updates
                for key, etag in current_state.items():
                    if key not in self.state:
                        logger.info(f"S3 DETECTED CREATE: {key}")
                        local_path = self._download_file(key)
                        chunks, embeddings = self.processor.process_file(local_path)
                        if chunks and embeddings:
                            self.db.upsert_document(key, chunks, embeddings)
                            
                    elif self.state[key] != etag:
                        logger.info(f"S3 DETECTED MODIFY: {key}")
                        self.db.delete_document(key)
                        local_path = self._download_file(key)
                        chunks, embeddings = self.processor.process_file(local_path)
                        if chunks and embeddings:
                            self.db.upsert_document(key, chunks, embeddings)

                # 2. Detect Deletes
                for key in list(self.state.keys()):
                    if key not in current_state:
                        logger.info(f"S3 DETECTED DELETE: {key}")
                        self.db.delete_document(key)

                # Update memory and wait before polling again
                self.state = current_state
                time.sleep(3) 
                
        except KeyboardInterrupt:
            logger.info("Cloud Watcher shutting down gracefully.")

if __name__ == "__main__":
    watcher = S3Watcher("enterprise-knowledge")
    watcher.poll()