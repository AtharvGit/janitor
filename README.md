# Automated Knowledge Janitor (ETL Pipeline for RAG)

An enterprise-grade, event-driven Data Engineering pipeline designed to automatically synchronize unstructured cloud document stores with a ChromaDB vector space, ensuring 100% data parity and zero orphaned vectors.

## 🏗️ Architecture & Features
* **Cloud Event Watcher:** Uses `boto3` and an automated polling loop to monitor an AWS S3 bucket (simulated locally via LocalStack) for `Create`, `Modify`, and `Delete` events.
* **Idempotent Vector Sync:** Guarantees database integrity. If a file is updated, old vector chunks are purged before new ones are embedded, preventing data duplication.
* **Semantic Chunking:** Utilizes Langchain to intelligently split text documents, preserving context before routing through the Google Gemini embedding model.
* **Resilience:** Implements `@retry` exponential backoff logic to gracefully handle rate limits or API downtime.
* **FastAPI Microservice:** Exposes a clean REST endpoint (`/query`) to allow frontend applications to search the semantic vector space.

## 🚀 Quickstart (Local Infrastructure)
This project uses Docker to simulate cloud infrastructure locally.

1. **Start the Infrastructure (ChromaDB + LocalStack S3)**
   ```bash
   docker-compose up -d