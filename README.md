# 10-K Financial Document Q&A System

A complete Retrieval-Augmented Generation (RAG) system that allows users to ask natural language questions about SEC 10-K financial reports and receive accurate, source-grounded answers through a modern web interface.

## Overview

This system demonstrates a **custom RAG implementation built from scratch** without using high-level RAG frameworks. It processes SEC 10-K reports, creates semantic embeddings, and provides intelligent question-answering through a complete web application. The implementation showcases the fundamental components of RAG architecture using core libraries and custom integration logic.

## Features

✅ **Complete RAG Pipeline** (All 4 phases implemented)
- **Document Processing**: Ingests HTML 10-K reports and extracts clean text content
- **Semantic Search**: Uses sentence transformers to create embeddings and find relevant document sections
- **LLM Integration**: Gemini API for intelligent answer synthesis with source citations
- **Web Frontend**: Modern single-page application with trust & safety features
- **Vector Database**: ChromaDB for efficient similarity search and retrieval
- **Containerized**: Docker Compose setup with dedicated services and profiles

🔧 **Custom RAG Implementation**
- Built from scratch using core libraries (no LangChain, LlamaIndex, or similar frameworks)
- Direct API integration with embedding models and LLMs
- Custom retrieval logic and context assembly
- Hand-crafted prompt engineering for optimal results

## Architecture

### Complete Implementation (All 4 Phases Complete)

**Phase 1: Data Ingestion Pipeline**
- HTML document parsing with BeautifulSoup for clean text extraction
- Semantic chunking using RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
- Local embedding generation with `all-MiniLM-L6-v2` sentence transformer
- Batch processing and storage in ChromaDB vector database

**Phase 2: RAG Core API**
- FastAPI service with custom retrieval logic
- Query embedding generation using the same model as ingestion
- Vector similarity search through ChromaDB HTTP API
- Context assembly from retrieved document chunks

**Phase 3: LLM Integration**
- Direct integration with Google Gemini API for answer synthesis
- Custom prompt engineering with source-grounded instructions
- Structured response format with answers and source citations
- Error handling for API limits and quota management

**Phase 4: Frontend UI**
- Single-page HTML application with Tailwind CSS
- Interactive question-answer interface with collapsible source citations
- Trust & safety features: disclaimers, source verification, feedback mechanisms
- Same-origin API integration with proper error handling

## Custom RAG Implementation Details

This project implements RAG **from first principles** without relying on high-level frameworks:

### Why Custom Implementation?
- **Educational Value**: Demonstrates core RAG concepts and implementation patterns
- **Full Control**: Complete visibility into each step of the retrieval and generation process
- **Optimization**: Direct tuning of embedding, retrieval, and prompt strategies
- **Transparency**: Clear understanding of how each component contributes to the final answer

### Core RAG Components Built From Scratch:

**1. Document Processing (`app/ingest.py`)**
```python
# Custom chunking strategy
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_text(text)

# Direct embedding generation
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = embedding_model.encode(batch_chunks).tolist()
```

**2. Retrieval Logic (`app/main.py:90-125`)**
```python
# Query embedding
question_embedding = embedding_model.encode(request.question).tolist()

# Vector similarity search
results = collection.query(
    query_embeddings=[question_embedding],
    n_results=request.top_k
)

# Context assembly
context = "\n\n---\n\n".join(retrieved_documents)
```

**3. Generation Pipeline (`app/main.py:126-157`)**
```python
# Custom prompt construction
prompt = f"""Context: {context}\nQuestion: {question}\nAnswer:"""

# Direct LLM API call
response = generation_model.generate_content(prompt)
```

**4. End-to-End Integration**
- Lazy loading for memory optimization
- Error handling and fallback strategies
- Structured response format with source attribution
- Frontend integration with same-origin API calls

## Getting Started

### Prerequisites
- Docker and Docker Compose
- At least 4GB available RAM (recommended for smooth operation)
- Google Gemini API key (for LLM integration)

### Quick Start

1. **Clone and navigate to the project**:
   ```bash
   git clone <repository-url>
   cd 10-k
   ```

2. **Set up environment variables**:
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key-here"
   ```

3. **Start all services**:
   ```bash
   docker compose up -d --build
   ```

4. **Run data ingestion** (one-time setup):
   ```bash
   docker compose --profile ingest up ingestion_runner
   ```

5. **Access the web application**:
   - Open your browser and go to: **http://localhost:8000**
   - Ask questions like "What is Google's revenue?" or "What are the main risk factors?"

### Alternative: API-Only Testing

If you prefer to test via API without the frontend:
```bash
# Test API health
curl http://localhost:8000/health

# Query the 10-K document
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Google'\''s revenue?", "top_k": 5}'
```

### Testing Without Gemini API Key

For development or when API quota is exceeded:
```bash
# Enable mock mode (bypasses Gemini API calls)
MOCK_MODE=true docker compose up -d --build
```

## API Endpoints

### GET `/`
Serves the frontend web application.

### GET `/health`
API health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "message": "10-K Q&A API is running."
}
```

### POST `/query`
Query the 10-K document and receive AI-generated answers with source citations.

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
  "answer": "Based on the retrieved information from Google's 10-K report, Google's revenue for 2023 was...",
  "sources": [
    {
      "content": "Relevant text chunk from the 10-K report that supports the answer...",
      "source_id": 1
    }
  ]
}
```

## Services

- **Frontend Web App**: `http://localhost:8000`
- **API Health Check**: `http://localhost:8000/health`
- **ChromaDB Admin**: `http://localhost:8001`

## Project Structure

```
10-k/
├── app/
│   ├── main.py              # FastAPI application with API endpoints and static serving
│   ├── ingest.py            # Data ingestion script with custom RAG processing
│   ├── check_db.py          # Database verification utility
│   ├── static/
│   │   └── index.html       # Complete frontend web application
│   └── goog-20231231.htm    # Sample Google 10-K report (test data)
├── docker-compose.yml       # Service orchestration with profiles
├── Dockerfile.api          # API container configuration
├── requirements.txt        # Python dependencies (core libraries only)
├── CLAUDE.md               # Development guide for Claude Code
└── README.md              # This file
```

## Technical Implementation

### Custom RAG Pipeline Components

**Document Processing**
- **Parser**: BeautifulSoup for HTML extraction and cleaning
- **Chunker**: LangChain's RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
- **Embeddings**: HuggingFace `all-MiniLM-L6-v2` sentence transformer (384 dimensions)
- **Storage**: ChromaDB collection `google_10k_2023` with HTTP client

**Retrieval System**
- **Query Processing**: Same embedding model as ingestion for consistency
- **Search**: ChromaDB cosine similarity search with configurable top-k
- **Context Assembly**: Custom concatenation with separators for LLM consumption

**Generation Pipeline**
- **LLM**: Google Gemini-1.5-flash via direct API integration
- **Prompting**: Custom system prompt with source-grounding instructions
- **Response**: Structured format with answer and source attribution

**Frontend Integration**
- **Framework**: Vanilla JavaScript with Tailwind CSS (no React/Vue)
- **API Calls**: Native fetch() with same-origin requests (no CORS needed)
- **UI Components**: Custom collapsible sections, feedback buttons, error handling

### Performance Optimizations
- **Lazy Loading**: Models loaded on first request to prevent startup OOM
- **Batch Processing**: Ingestion processes 50 chunks at a time
- **Memory Management**: 4GB container limits with 8GB swap for model loading
- **Caching**: Persistent ChromaDB storage with Docker volumes

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