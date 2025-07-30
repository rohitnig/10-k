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
- `app/main.py`: FastAPI application with `/query` endpoint for answer synthesis using Gemini API, static file serving, and CORS configuration
- `app/ingest.py`: Data ingestion script that processes HTML 10-K reports and loads them into ChromaDB
- `app/static/index.html`: Complete frontend web application with trust & safety features
- `app/goog-20231231.htm`: Google's 2023 10-K report used as test data
- `docker-compose.yml`: Orchestrates FastAPI backend, ChromaDB, and dedicated ingestion service with profiles
- `Dockerfile.api`: Container configuration for the FastAPI application

## Development Commands

### Running the Application
```bash
# Start all services (API + ChromaDB only)
docker compose up -d --build

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f api
docker compose logs -f chromadb
```

### Data Ingestion
```bash
# Automated ingestion using dedicated service (recommended)
docker compose --profile ingest up ingestion_runner

# Manual ingestion inside API container (legacy method)
docker compose exec api python ingest.py
```

### Frontend Access
- **Web Interface**: http://localhost:8000
- **API Health Check**: http://localhost:8000/health
- **ChromaDB**: http://localhost:8001

### Development
```bash
# Install dependencies locally for development
pip install -r requirements.txt

# Run FastAPI locally (requires ChromaDB running)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing and Development Modes
```bash
# Enable mock mode for testing without Gemini API (bypasses quota limits)
MOCK_MODE=true docker compose up -d --build

# Run with memory profiling and debugging
PYTHONFAULTHANDLER=1 docker compose up -d --build

# Check container status
docker compose ps
```

## Key Implementation Details

### Core Architecture Pattern
The system uses lazy loading across all major components to optimize memory usage and prevent startup failures:
- **AppState Class**: Centralized state management in `app/main.py:26-57` that defers expensive operations
- **Lazy Model Loading**: Embedding model, ChromaDB connection, and Gemini API are initialized only on first use
- **Error Boundary**: Each lazy loader includes proper error handling and logging

### Embedding Strategy
- Uses `all-MiniLM-L6-v2` sentence transformer model
- Semantic chunking with RecursiveCharacterTextSplitter (1000 char chunks, 200 char overlap)
- Embeddings generated locally, not via external API
- Batch processing (batch_size=50) during ingestion to manage memory constraints

### Data Processing
- HTML 10-K reports are parsed with BeautifulSoup to extract clean text (`app/ingest.py:14-27`)
- Script and style tags are removed before text extraction
- ChromaDB collection name: `google_10k_2023`
- Ingestion is idempotent - skips re-processing if collection already populated (`app/ingest.py:52-54`)

### API Design
**POST `/query`** - Main query endpoint (`app/main.py:80-138`):
- **Request**: `QueryRequest` model with `question: str` and `top_k: int = 5`
- **Response**: `QueryResponse` model with `answer: str` and `sources: list[SourceDocument]`
- **Process Flow**:
  1. Generate embedding for user question using sentence transformer
  2. Query ChromaDB for top_k most relevant chunks
  3. Construct context-rich prompt for Gemini API
  4. Synthesize answer using Gemini-1.5-flash model
  5. Return structured response with answer and source citations
- Includes rate limiting (429) and error handling (500) responses
- All responses are grounded in retrieved 10-K document chunks

**GET `/`** - Serves the frontend HTML application

**GET `/health`** - API health check endpoint returns system status

### Frontend Implementation
**Technology Stack**: Single HTML file using Tailwind CSS and vanilla JavaScript
- **Location**: `app/static/index.html`
- **API Integration**: Makes relative URL requests to `/query` endpoint (same-origin)
- **Features**: Question input, answer display, collapsible source citations, feedback buttons
- **Trust Elements**: Prominent disclaimer, source verification UI, feedback logging to console
- **Responsive Design**: Mobile-friendly interface with clean typography
- **Error Handling**: Network errors, API failures, and user-friendly error messages

### Trust & Verifiability
The project emphasizes trust and verifiability over simple functionality:
- All answers must be grounded in source material
- Source citations are required for any LLM-generated responses
- UI must display disclaimers about AI-generated content
- Feedback mechanisms for user validation

## Environment Variables
- `CHROMA_HOST`: ChromaDB hostname (defaults to "localhost", set to "chromadb" in Docker)
- `GEMINI_API_KEY`: Required for LLM integration - must be set for `/query` endpoint to function
- `MOCK_MODE`: Set to "true" to bypass Gemini API calls for testing (defaults to "false")
- `PYTHONFAULTHANDLER`: Set to 1 for enhanced error debugging in containers

## Critical Development Notes

### Adding New Dependencies
When adding new Python packages:
1. Add to `requirements.txt` with pinned versions
2. Rebuild containers: `docker compose up --build`
3. Test that lazy loading still works properly

### Modifying Data Sources
To use different 10-K reports:
1. Place HTML file in `app/` directory
2. Update `SOURCE_DOCUMENT_PATH` in `app/ingest.py:10`
3. Update `COLLECTION_NAME` in both `app/main.py:14` and `app/ingest.py:12`
4. Run ingestion: `docker compose --profile ingest up ingestion_runner`

### Memory Considerations
- Container has 2GB shared memory (`shm_size: '2gb'`) and 4GB memory limit (`mem_limit: 4g`)
- Sentence transformer model (~90MB) loaded on first query request
- ChromaDB client connection established lazily
- Batch size of 50 chunks during ingestion prevents OOM errors
- Swap limit set to 8GB for handling memory spikes during model loading

## Memory Management & Performance
The application uses lazy loading to optimize memory usage:
- **Embedding Model**: Loaded only on first query request (prevents startup OOM)
- **ChromaDB Connection**: Established on demand
- **Gemini API**: Initialized when first needed
- **Container Memory**: 2GB shared memory allocated via `shm_size` in docker-compose
- **Batch Processing**: Ingestion processes chunks in batches to manage memory

## Security Considerations
- **API Key Management**: GEMINI_API_KEY is passed via environment variables
- **No Authentication**: API endpoints are publicly accessible
- **Input Validation**: Basic validation on query parameters only

## Current Implementation Status
**Phase 4 Complete**: The system now includes a complete web frontend with full RAG pipeline. All planned features have been implemented. Key completed features:
- Complete RAG pipeline with ChromaDB vector storage
- Gemini-1.5-flash integration for answer generation with mock mode support
- **Frontend Web Application**: Single-page HTML application with Tailwind CSS
- **Trust & Safety Features**: Disclaimers, source citations, and feedback mechanisms
- **Static File Serving**: FastAPI serves frontend and handles API requests
- **CORS Configuration**: Proper cross-origin support for API calls
- Error handling for API rate limits and quota exceeded scenarios
- Lazy loading for memory optimization
- Docker Compose profiles for dedicated ingestion service

## Debugging and Validation Commands

### Database Verification
```bash
# Check ChromaDB collection status and document count
docker compose exec api python check_db.py

# Verify ingestion completed successfully
curl http://localhost:8001/api/v1/collections/google_10k_2023

# Manually check collection via ChromaDB API
curl http://localhost:8001/api/v1/collections/google_10k_2023/count
```

### API Testing
```bash
# Test frontend (should serve HTML page)
curl -s http://localhost:8000/ | head -n 5

# Test API health endpoint
curl http://localhost:8000/health

# Test query endpoint with sample question (requires GEMINI_API_KEY or MOCK_MODE=true)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Google'\''s revenue?", "top_k": 5}'

# Test rate limiting behavior
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main business risks?", "top_k": 3}'

# Test with minimal parameters (top_k defaults to 5)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Who are Google'\''s competitors?"}'
```

### Service Monitoring
```bash
# Monitor API logs
docker compose logs -f api

# Monitor ChromaDB logs
docker compose logs -f chromadb

# Check container health
docker compose ps

# Monitor all services
docker compose logs -f
```

## Common Issues and Solutions

### Gemini API Quota Exceeded
If you see "429 You exceeded your current quota" errors:
1. **Immediate Fix**: Enable mock mode: `MOCK_MODE=true docker compose up -d --build`
2. **Long-term**: Wait for quota reset (midnight Pacific Time) or upgrade Gemini API plan
3. **Free Tier Limits**: 1,500 requests per day, 15 requests per minute

### CORS Errors in Browser
If you see "Cross-Origin Request Blocked" errors:
1. Ensure you're accessing the frontend via `http://localhost:8000` (not file:// or different port)
2. The JavaScript uses relative URLs for same-origin requests
3. CORS middleware is configured in `app/main.py` for cross-origin scenarios

### Memory Issues
If containers crash with OOM errors:
1. Check available system memory (requires ~4GB for smooth operation)
2. Memory limits are set to 4GB per container with 8GB swap
3. Lazy loading prevents most startup memory issues