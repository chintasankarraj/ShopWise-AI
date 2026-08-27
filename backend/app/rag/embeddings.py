import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


# ============================================================
# SHARED GEMINI EMBEDDING CONFIGURATION
#
# Both ingest.py and retriever.py import from this module so
# documents and queries are always embedded with the same
# model and the same output dimensionality -- required for
# ChromaDB similarity search to be meaningful.
#
# This replaces the previous sentence-transformers/PyTorch
# embedding model, which was loading a full local model into
# memory at import time and was the cause of the Render OOM.
# ============================================================

EMBEDDING_MODEL = "gemini-embedding-001"

EMBEDDING_DIMENSIONS = 768

# Explicit HTTP timeout required -- see the identical comment in
# insights_agent.py/alternative_agent.py. Shorter than the main
# generation timeout since embedding calls are lightweight and
# should return quickly under normal conditions.
_GEMINI_EMBEDDING_TIMEOUT_MS = 15_000

api_key = os.getenv("GEMINI_API_KEY")

client = (
    genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=_GEMINI_EMBEDDING_TIMEOUT_MS
        ),
    )
    if api_key
    else None
)


# ============================================================
# DOCUMENT EMBEDDINGS (ingestion)
#
# Ingestion is a deploy-time/manual step, not a live request,
# so failures here are allowed to raise loudly instead of
# degrading silently -- an empty knowledge base should never
# ship unnoticed.
# ============================================================

def embed_documents(texts):

    if client is None:

        raise RuntimeError(
            "GEMINI_API_KEY is required to generate embeddings "
            "for RAG ingestion."
        )

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )

    return [
        embedding.values
        for embedding in response.embeddings
    ]


# ============================================================
# QUERY EMBEDDING (live retrieval)
#
# Retrieval happens on a live /analyze request, so it must
# degrade to "no context" instead of raising -- consistent
# with how the rest of retriever.py already handles a missing
# collection.
# ============================================================

def embed_query(text):

    if client is None:
        return None

    try:

        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=EMBEDDING_DIMENSIONS,
            ),
        )

        return response.embeddings[0].values

    except Exception as error:

        print(
            "Gemini query embedding failed:",
            error
        )

        return None
