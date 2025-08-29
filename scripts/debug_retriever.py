import pprint
from src.config_loader import load_config
from src.embeddings import build_embeddings
from src.vectorstore import connect_milvus, get_vectorstore, make_retriever


def test_retrieval():
    """
    Tests the retriever in isolation to see what documents it fetches for a query.
    """
    print("--- Loading Configuration ---")
    cfg = load_config()
    app_cfg = cfg["app"]

    # A sample question that should have a clear answer in your handbook
    test_question = "What is the company's policy on sick leave?"
    print(f"--- Test Question: '{test_question}' ---")

    try:
        print("\n--- Building Embeddings Model ---")
        embeddings = build_embeddings(app_cfg["embedding"])

        print("\n--- Connecting to Milvus ---")
        connect_milvus(app_cfg["milvus"])

        print("\n--- Getting Vector Store and Retriever ---")
        vector_store = get_vectorstore(embeddings, app_cfg["milvus"])

        # Use the same 'candidates' number as in your main app
        candidates = int(app_cfg.get("reranker", {}).get("candidates", 4))
        retriever = make_retriever(vector_store, {"k": candidates})

        print("\n--- Invoking Retriever ---")
        retrieved_docs = retriever.invoke(test_question)

        print(f"\n--- Found {len(retrieved_docs)} documents ---")

        if not retrieved_docs:
            print("\n[FAIL] The retriever returned ZERO documents.")
            print("Possible reasons:")
            print("1. Data was not ingested correctly. Re-run 'python -m scripts.ingest'.")
            print("2. The collection name in 'config/app.yaml' might be wrong.")
            print("3. There is no relevant information about the question in your documents.")
            return

        print("\n--- [SUCCESS] Retrieved Documents: ---")
        for i, doc in enumerate(retrieved_docs):
            print(f"\n----- Document {i + 1} (Metadata: {doc.metadata}) -----")
            # Print the first 300 characters of the content
            pprint.pprint(doc.page_content[:300] + "...")

    except Exception as e:
        print(f"\n[ERROR] An exception occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_retrieval()