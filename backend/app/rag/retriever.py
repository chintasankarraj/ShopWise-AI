from pathlib import Path

import chromadb

from app.rag.embeddings import embed_query


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CHROMA_DIR = BASE_DIR / "chroma_db"


# ============================================================
# CHROMA
#
# Deployment initialization strategy:
# `ingest.py` must be run at least once (locally, in a build
# step, or as a one-off startup task) to create and populate
# the "shopwise_knowledge" collection before this module is
# imported. If that hasn't happened yet -- e.g. `chroma_db/`
# wasn't shipped to a fresh deploy target -- `collection` is
# left as None below instead of crashing the import, and RAG
# degrades to "no retrieved context" rather than taking down
# the whole backend on startup.
# ============================================================

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

try:

    collection = client.get_collection(
        name="shopwise_knowledge"
    )

except Exception as error:

    print(
        "RAG collection 'shopwise_knowledge' was not found: "
        f"{error}"
    )

    print(
        "Run `python -m app.rag.ingest` (from backend/) to "
        "build it. RAG retrieval will return no context "
        "until then."
    )

    collection = None


# ============================================================
# RETRIEVE
# ============================================================

def retrieve_context(
    query: str,
    top_k: int = 3,
):
    """
    Retrieve the most relevant knowledge chunks
    for a user/product query.
    """

    if not query or not query.strip():
        return []

    if collection is None:
        return []

    query_embedding = embed_query(
        query
    )

    if query_embedding is None:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    retrieved = []

    for document, metadata in zip(
        documents,
        metadatas,
    ):

        retrieved.append(
            {
                "text": document,
                "source": (
                    metadata.get(
                        "source",
                        "Unknown"
                    )
                    if metadata
                    else "Unknown"
                ),
            }
        )

    return retrieved


# ============================================================
# FORMAT CONTEXT
# ============================================================

def format_context(
    retrieved_context,
):
    """
    Convert retrieved chunks into a clean
    context block for the LLM.
    """

    if not retrieved_context:
        return (
            "No relevant knowledge was retrieved."
        )

    sections = []

    for index, item in enumerate(
        retrieved_context,
        start=1,
    ):

        sections.append(
            f"""
SOURCE {index}
------------
{item["text"]}
"""
        )

    return "\n".join(sections)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    query = (
        "OnePlus smartphone with "
        "7000mAh battery and 144Hz LCD display"
    )

    print()
    print("=" * 80)
    print("SHOPWISE RAG RETRIEVAL TEST")
    print("=" * 80)

    print()
    print("QUERY:")
    print(query)

    print()

    results = retrieve_context(
        query,
        top_k=3,
    )

    print(
        f"Retrieved chunks: {len(results)}"
    )

    print()

    for index, item in enumerate(
        results,
        start=1,
    ):

        print("-" * 80)
        print(
            f"RESULT #{index}"
        )
        print(
            f"Source: {item['source']}"
        )
        print()
        print(
            item["text"]
        )

    print()
    print("=" * 80)