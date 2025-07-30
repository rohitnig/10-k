# 10-K Financial Document Q&A System

A Retrieval-Augmented Generation (RAG) system that allows users to ask natural language questions about SEC 10-K financial reports and receive accurate, source-grounded answers.

## Overview

This system processes SEC 10-K reports, creates semantic embeddings of the content, and enables intelligent querying through a FastAPI backend. Built as an MVP demonstration of RAG architecture for financial document analysis.

## Features

- **Document Processing**: Ingests HTML 10-K reports and extracts clean text content
- **Semantic Search**: Uses sentence transformers to create embeddings and find relevant document sections
- **RESTful API**: FastAPI backend with `/query` endpoint for retrieving relevant document chunks
- **Vector Database**: ChromaDB for efficient similarity search and retrieval
- **Containerized**: Docker Compose setup for easy deployment and development

## Architecture

### Current Implementation (Phase 2)
- **Data Ingestion Pipeline**: Downloads and processes 10-K reports, chunks them semantically, generates embeddings using `all-MiniLM-L6-v2`, and stores them in ChromaDB
- **RAG Core API**: FastAPI service that handles query embedding and context retrieval from ChromaDB
- **Vector Storage**: ChromaDB for storing document embeddings and metadata

### Planned Features (Future Phases)
- **LLM Integration**: Integration with Gemini API for answer synthesis with source citations
- **Frontend UI**: Single-page application with trust & safety features
- **Enhanced Metadata**: Page numbers, sections, and improved source tracking

## Getting Started

### Prerequisites
- Docker and Docker Compose
- At least 2GB available RAM

### Quick Start

1. **Clone and navigate to the project**:
   ```bash
   git clone <repository-url>
   cd 10-k
   ```

2. **Start the services**:
   ```bash
   docker-compose up --build
   ```

3. **Ingest the sample 10-K report**:
   ```bash
   docker-compose exec api python ingest.py
   ```

4. **Test the API**:
   ```bash
   # Health check
   curl http://localhost:8000/

   # Query the 10-K document
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"question": "What is Google'\''s revenue?", "top_k": 5}'
   ```

## API Endpoints

### GET `/`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "message": "10-K Q&A API is running."
}
```

### POST `/query`
Query the 10-K document for relevant information.

**Request:**
```json
{
  "question": "What is Google's revenue?",
  "top_k": 5
}
```

**Response:**
```json
{
  "retrieved_chunks": [
    {
      "content": "Relevant text chunk from the 10-K report..."
    }
  ]
}
```

## Services

- **FastAPI Backend**: `http://localhost:8000`
- **ChromaDB**: `http://localhost:8001`

## Project Structure

```
10-k/
├── app/
│   ├── main.py              # FastAPI application
│   ├── ingest.py            # Data ingestion script
│   └── goog-20231231.htm    # Sample Google 10-K report
├── docker-compose.yml       # Service orchestration
├── Dockerfile.api          # API container configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Technical Details

### Embedding Strategy
- **Model**: `all-MiniLM-L6-v2` sentence transformer
- **Chunking**: RecursiveCharacterTextSplitter (1000 char chunks, 200 char overlap)
- **Storage**: ChromaDB collection `google_10k_2023`

### Memory Optimization
- Lazy loading of ML models to prevent startup OOM issues
- Batch processing during ingestion
- Configurable batch sizes for different memory constraints

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run FastAPI locally (requires ChromaDB running)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Environment Variables
- `CHROMA_HOST`: ChromaDB hostname (defaults to "localhost", set to "chromadb" in Docker)

### Adding New 10-K Reports
1. Place the HTML file in the `app/` directory
2. Update `SOURCE_DOCUMENT_PATH` in `ingest.py`
3. Run the ingestion script

## Trust & Verifiability

This system emphasizes trust and verifiability:
- All responses are grounded in source material from the actual 10-K report
- Retrieved chunks include the original text content for verification
- Future versions will include source citations and page references

## Troubleshooting

### Container Memory Issues
If the API container crashes during startup:
- Ensure at least 2GB RAM is available
- The system uses lazy loading to minimize memory usage

### Encoding Issues
If you encounter UTF-8 decode errors during ingestion:
- Some 10-K files may use different encodings
- The system attempts multiple encoding strategies automatically

## License

This project is for educational and demonstration purposes.