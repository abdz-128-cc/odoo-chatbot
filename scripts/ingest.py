from src.ingest import run_ingest
if __name__ == "__main__":
    """
    Ingests documents into the vector store.

    Loads configuration, processes documents from the handbook directory,
    chunks them, builds embeddings, connects to Milvus, and upserts chunks.
    """
    run_ingest()
