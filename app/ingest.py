import os
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
import time
import traceback

# --- CONFIGURATION ---
SOURCE_DOCUMENT_PATH = "goog-20231231.htm" 
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
COLLECTION_NAME = "google_10k_2023"

def read_and_parse_local_10k(file_path):
    print(f"Reading local 10-K report from {file_path}...")
    full_path = os.path.join("/app", file_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"The file was not found at {full_path}. Make sure it's inside the 'app' folder.")
    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()
    print("Parsing HTML content...")
    soup = BeautifulSoup(html_content, 'html.parser')
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
    text = soup.get_text(separator='\n', strip=True)
    print(f"Extracted {len(text)} characters of text.")
    return text

def chunk_text(text):
    print("Chunking text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    print(f"Created {len(chunks)} chunks.")
    return chunks

def embed_and_load(chunks):
    try:
        print("--- Step 1: Initializing embedding model (this may take a moment)... ---")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("--- Step 2: Embedding model loaded successfully. ---")

        print(f"--- Step 3: Connecting to ChromaDB at {CHROMA_HOST}... ---")
        client = chromadb.HttpClient(host=CHROMA_HOST, port=8000)
        print("--- Step 4: Connected to ChromaDB. ---")
        
        print(f"--- Step 5: Getting or creating collection: {COLLECTION_NAME}... ---")
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        if collection.count() > 0:
            print(f"Collection '{COLLECTION_NAME}' already contains documents. Skipping ingestion.")
            return
        print("--- Step 6: Collection is ready. ---")

        print("--- Step 7: Starting the embedding and loading process... ---")
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            print(f"  - Processing batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
            batch_chunks = chunks[i:i+batch_size]
            
            embeddings = embedding_model.encode(batch_chunks, show_progress_bar=False).tolist()
            
            ids = [f"chunk_{i+j}" for j in range(len(batch_chunks))]
            
            collection.add(
                documents=batch_chunks,
                embeddings=embeddings,
                ids=ids
            )
        
        print("\n--- SCRIPT FINISHED SUCCESSFULLY ---")
        print(f"Total documents in collection: {collection.count()}")

    except Exception as e:
        print("\n--- AN ERROR OCCURRED ---")
        print(f"Error of type {type(e).__name__}: {e}")
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    report_text = read_and_parse_local_10k(SOURCE_DOCUMENT_PATH)
    text_chunks = chunk_text(report_text)
    embed_and_load(text_chunks)

