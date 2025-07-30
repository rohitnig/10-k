# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a 10-K financial document Q&A system built as a RAG (Retrieval-Augmented Generation) MVP. The system allows users to ask natural language questions about SEC 10-K reports and receive accurate, source-grounded answers. It consists of a FastAPI backend, ChromaDB vector database, and is designed to be deployed with Docker Compose.

## Architecture

The system follows a 4-phase development plan:

1. **Data Ingestion Pipeline**: Downloads and processes 10-K reports, chunks them semantically, generates embeddings using all-MiniLM-L6-v2, and stores them in ChromaDB
2. **RAG Core API**: FastAPI service that handles query embedding and context retrieval from ChromaDB
3. **LLM Integration**: Integration with Gemini API for answer synthesis with source citations
4. **Frontend UI**: Single-page application with trust & safety features

Key components:
- `app/main.py`: FastAPI application with `/query` endpoint for retrieving relevant document chunks
- `app/ingest.py`: Data ingestion script that processes HTML 10-K reports and loads them into ChromaDB
- `app/goog-20231231.htm`: Google's 2023 10-K report used as test data
- `docker-compose.yml`: Orchestrates FastAPI backend and ChromaDB services
- `Dockerfile.api`: Container configuration for the FastAPI application

## Development Commands

### Running the Application
```bash
# Start all services
docker-compose up --build

# Start in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f
```

### Data Ingestion
```bash
# Run the ingestion script inside the API container
docker-compose exec api python ingest.py
```

### Development
```bash
# Install dependencies locally for development
pip install -r requirements.txt

# Run FastAPI locally (requires ChromaDB running)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Services and Ports
- FastAPI backend: http://localhost:8000
- ChromaDB: http://localhost:8001
- API health check: http://localhost:8000/

## Key Implementation Details

### Embedding Strategy
- Uses `all-MiniLM-L6-v2` sentence transformer model
- Semantic chunking with RecursiveCharacterTextSplitter (1000 char chunks, 200 char overlap)
- Embeddings generated locally, not via external API

### Data Processing
- HTML 10-K reports are parsed with BeautifulSoup to extract clean text
- ChromaDB collection name: `google_10k_2023`
- Ingestion is idempotent - skips re-processing if collection already populated

### API Design
- `/query` endpoint accepts JSON with `question` and optional `top_k` parameters
- Returns structured JSON with retrieved document chunks and metadata
- Currently returns raw retrieved chunks (Phase 2), not LLM-synthesized answers

### Trust & Verifiability
The project emphasizes trust and verifiability over simple functionality:
- All answers must be grounded in source material
- Source citations are required for any LLM-generated responses
- UI must display disclaimers about AI-generated content
- Feedback mechanisms for user validation

## Environment Variables
- `CHROMA_HOST`: ChromaDB hostname (defaults to "localhost", set to "chromadb" in Docker)

## Current Implementation Status
Based on the code analysis, the project appears to be in Phase 2 - the core RAG API is implemented but LLM integration for answer synthesis is not yet complete. The system can retrieve relevant chunks from the 10-K report but does not yet generate natural language answers.