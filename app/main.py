import os
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb
import logging

# --- CONFIGURATION ---
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
COLLECTION_NAME = "google_10k_2023"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'

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

app_state = AppState()
app = FastAPI()

# --- API DATA MODELS ---
class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

class Document(BaseModel):
    content: str
    # In a real app, you'd include more metadata like page number, source, etc.

class QueryResponse(BaseModel):
    retrieved_chunks: list[Document]

# --- API ENDPOINTS ---
@app.get("/")
def read_root():
    """A simple health check endpoint."""
    return {"status": "ok", "message": "10-K Q&A API is running."}

@app.post("/query", response_model=QueryResponse)
def query_10k(request: QueryRequest):
    """
    Receives a question, embeds it, and retrieves the most relevant
    text chunks from the 10-K report stored in ChromaDB.
    """
    logger.info(f"Received query: '{request.question}'")

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

    # 3. Format and return the retrieved chunks.
    # We get a list of lists, so we take the first element.
    retrieved_documents = [Document(content=doc) for doc in results['documents'][0]]
    
    logger.info(f"Successfully retrieved {len(retrieved_documents)} chunks.")
    
    return {"retrieved_chunks": retrieved_documents}


