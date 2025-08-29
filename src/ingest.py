from __future__ import annotations
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from .config_loader import load_config
from .embeddings import build_embeddings
from .vectorstore import connect_milvus, get_vectorstore, create_or_update
from .loaders import walk_docs

def chunk(docs: List[Document], ccfg: dict) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=ccfg.get("chunk_size", 700),
        chunk_overlap=ccfg.get("chunk_overlap", 100),
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(docs)
    # add useful metadata
    for i, d in enumerate(chunks):
        d.metadata["chunk_id"] = i
    return chunks

def run_ingest():
    cfg = load_config()
    app, prompts = cfg["app"], cfg["prompts"]

    # Load files (PDF/DOCX, easy to extend)
    base_dir = app["data"]["handbook_dir"]
    raw_docs = walk_docs(base_dir)
    if not raw_docs:
        print("No documents found in", base_dir); return

    # Chunk
    pieces = chunk(raw_docs, app["chunking"])

    # Embeddings + Milvus
    emb = build_embeddings(app["embedding"])
    connect_milvus(app["milvus"])
    vs = get_vectorstore(emb, app["milvus"])


    # Upsert
    create_or_update(vs, pieces)
    print(f"Ingested {len(pieces)} chunks into Milvus collection '{app['milvus']['collection']}'")


if __name__ == "__main__":
    run_ingest()
