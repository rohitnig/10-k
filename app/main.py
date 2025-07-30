import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb
import logging
import google.generativeai as genai

# --- CONFIGURATION ---
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
COLLECTION_NAME = "google_10k_2023"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not found in environment variables")

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- APPLICATION STATE ---
# We lazy load the model to avoid memory issues at startup
class AppState:
    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.generation_model = None
        logger.info("AppState initialized - models will be loaded on first request")

    def get_embedding_model(self):
        if self.embedding_model is None:
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info("Embedding model loaded.")
        return self.embedding_model

    def get_collection(self):
        if self.collection is None:
            logger.info(f"Connecting to ChromaDB at {CHROMA_HOST}...")
            self.chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=8000)
            self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
            logger.info(f"Connected to ChromaDB and got collection '{COLLECTION_NAME}'.")
        return self.collection
    
    def get_generation_model(self):
        if self.generation_model is None:
            if not GEMINI_API_KEY:
                raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
            logger.info("Initializing Gemini generation model...")
            self.generation_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini generation model initialized.")
        return self.generation_model

app_state = AppState()
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- API DATA MODELS ---
class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

class SourceDocument(BaseModel):
    content: str
    source_id: int

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]

# --- API ENDPOINTS ---
@app.get("/")
def serve_frontend():
    """Serve the frontend HTML application."""
    return FileResponse("static/index.html")

@app.get("/health")
def health_check():
    """API health check endpoint."""
    return {"status": "ok", "message": "10-K Q&A API is running."}

@app.post("/query", response_model=QueryResponse)
def query_10k(request: QueryRequest):
    """
    Receives a question, embeds it, retrieves the most relevant
    text chunks from the 10-K report, and synthesizes an answer using Gemini.
    """
    logger.info(f"Received query: '{request.question}'")

    try:
        # 1. Generate an embedding for the user's question.
        embedding_model = app_state.get_embedding_model()
        question_embedding = embedding_model.encode(request.question).tolist()

        # 2. Query ChromaDB to find the most relevant document chunks.
        logger.info(f"Querying collection for {request.top_k} most relevant chunks...")
        collection = app_state.get_collection()
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=request.top_k
        )

        # 3. Extract and format the retrieved documents
        retrieved_documents = results['documents'][0]
        logger.info(f"Successfully retrieved {len(retrieved_documents)} chunks.")

        # Check if we're in mock mode (for testing when quota exceeded)
        if MOCK_MODE:
            logger.info("Running in MOCK_MODE - generating mock response")
            synthesized_answer = f"""Based on the retrieved information from Google's 10-K report, here's what I found regarding your question: "{request.question}"

This is a mock response for testing purposes. The actual answer would be synthesized from the following {len(retrieved_documents)} source documents that were retrieved from the vector database.

Key information includes financial data, business operations, risk factors, and strategic initiatives as detailed in the source citations below."""
        else:
            context = "\n\n---\n\n".join(retrieved_documents)
            prompt = f"""
            You are a highly skilled financial analyst assistant. Your task is to answer a user's question based only on the provided context from a company's 10-K report. Do not use any external knowledge.

            If the answer is not available in the context, you must state that you cannot answer the question with the information provided.

            Context from the 10-K report:
            ---
            {context}
            ---

            User's Question:
            {request.question}

            Synthesized Answer:
            """

            logger.info("Sending prompt to Gemini API for synthesis...")
            generation_model = app_state.get_generation_model()
            response = generation_model.generate_content(prompt)

            synthesized_answer = response.text.strip()
            logger.info(f"Received synthesized answer from Gemini.")

        source_docs = [SourceDocument(content=doc, source_id=i+1) for i, doc in enumerate(retrieved_documents)]

        return {"answer": synthesized_answer, "sources": source_docs}
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        if "429" in str(e) or "rate limit" in str(e).lower():
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail="Internal server error occurred while processing your query.")


