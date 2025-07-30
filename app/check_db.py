import chromadb
import os

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
COLLECTION_NAME = "google_10k_2023"

print(f"Connecting to ChromaDB at {CHROMA_HOST}...")
client = chromadb.HttpClient(host=CHROMA_HOST, port=8000)

try:
    collection = client.get_collection(name=COLLECTION_NAME)
    print(f"Successfully connected to collection '{COLLECTION_NAME}'.")

    count = collection.count()
    print(f"Total documents in collection: {count}")

    if count > 0:
        print("\n--- Retrieving first 2 documents ---")
        results = collection.get(
            ids=[f"chunk_{i}" for i in range(min(2, count))],
            include=["documents"]
        )
        for i, doc in enumerate(results['documents']):
            print(f"\n--- Document {i+1} ---")
            # Print the first 300 characters of the document
            print(doc[:300] + "...")

except Exception as e:
    print(f"\nAn error occurred: {e}")
