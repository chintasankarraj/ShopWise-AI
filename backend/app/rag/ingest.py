from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DOCUMENTS_DIR = BASE_DIR / "documents"

CHROMA_DIR = BASE_DIR / "chroma_db"


# ============================================================
# CHROMA
# ============================================================

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)


collection = client.get_or_create_collection(
    name="shopwise_knowledge"
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# ============================================================
# CHUNKING
# ============================================================

def chunk_text(
    text: str,
    chunk_size: int = 700,
    overlap: int = 100,
):
    """
    Split text into overlapping chunks.
    """

    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


# ============================================================
# LOAD DOCUMENTS
# ============================================================

def load_documents():

    documents = []

    for file_path in DOCUMENTS_DIR.glob("*.txt"):

        print(
            f"Reading: {file_path.name}"
        )

        text = file_path.read_text(
            encoding="utf-8"
        )

        chunks = chunk_text(text)

        for index, chunk in enumerate(chunks):

            documents.append(
                {
                    "id": (
                        f"{file_path.stem}"
                        f"-{index}"
                    ),
                    "text": chunk,
                    "source": file_path.name,
                }
            )

    return documents


# ============================================================
# INGEST
# ============================================================

def ingest():

    documents = load_documents()

    if not documents:

        print(
            "No documents found."
        )

        return

    print(
        f"Total chunks: {len(documents)}"
    )

    texts = [
        document["text"]
        for document in documents
    ]

    ids = [
        document["id"]
        for document in documents
    ]

    metadatas = [
        {
            "source": document["source"]
        }
        for document in documents
    ]

    print(
        "Creating embeddings..."
    )

    embeddings = embedding_model.encode(
        texts,
        show_progress_bar=True
    ).tolist()

    # --------------------------------------------------------
    # Clear existing collection
    # --------------------------------------------------------

    existing = collection.get()

    if existing["ids"]:

        collection.delete(
            ids=existing["ids"]
        )

    # --------------------------------------------------------
    # Store vectors
    # --------------------------------------------------------

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print()
    print("=" * 70)
    print("SHOPWISE RAG INGESTION COMPLETE")
    print("=" * 70)
    print(
        f"Documents stored: {len(documents)}"
    )
    print(
        f"ChromaDB path: {CHROMA_DIR}"
    )
    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    ingest()