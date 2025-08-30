# src/vectorstore.py
from __future__ import annotations
import os
from uuid import uuid4
from typing import List
from pymilvus import connections
from langchain_core.documents import Document
from langchain_milvus import Milvus

def connect_milvus(mcfg: dict):
    """
    Connects to Milvus or Zilliz based on configuration.

    Args:
        mcfg: The Milvus configuration.

    Raises:
        RuntimeError: If Zilliz credentials are missing.
    """
    alias = mcfg.get("alias", "default")
    if mcfg.get("use_zilliz", False):
        zid = os.getenv("ZILLIZ_ID")
        region = os.getenv("ZILLIZ_REGION")
        token = os.getenv("ZILLIZ_TOKEN")
        if not all([zid, region, token]):
            raise RuntimeError("ZILLIZ_ID, ZILLIZ_REGION, and ZILLIZ_TOKEN must be set in env")
        uri = f"https://{zid}.api.{region}.zillizcloud.com"
        connections.connect(alias=alias, uri=uri, token=token, secure=True)
    else:
        host = mcfg.get("host", "127.0.0.1")
        port = mcfg.get("port", "19530")
        connections.connect(alias=alias, host=host, port=port, secure=mcfg.get("secure", False))

def get_vectorstore(emb, mcfg: dict):
    """
    Creates or gets a Milvus vector store instance.

    Args:
        emb: The embeddings function.
        mcfg: The Milvus configuration.

    Returns:
        The Milvus vector store.

    Raises:
        RuntimeError: If Zilliz credentials are missing.
    """
    if mcfg.get("use_zilliz", False):
        zid = os.getenv("ZILLIZ_ID")
        region = os.getenv("ZILLIZ_REGION")
        token = os.getenv("ZILLIZ_TOKEN")
        if not all([zid, region, token]):
            raise RuntimeError("ZILLIZ_ID, ZILLIZ_REGION, and ZILLIZ_TOKEN must be set in env")
        uri = f"https://{zid}.api.{region}.zillizcloud.com"
        connection_args = {"uri": uri, "token": token, "secure": True}
    else:
        connection_args = {
            "host": mcfg.get("host", "127.0.0.1"),
            "port": mcfg.get("port", "19530"),
            "secure": mcfg.get("secure", False),
        }

    return Milvus(
        embedding_function=emb,
        connection_args=connection_args,   # <- no 'alias' here
        collection_name=mcfg["collection"],
        index_params=mcfg["index_params"],
        search_params=mcfg["search_params"],
    )

def make_retriever(vs, rcfg: dict):
    """
    Creates a retriever from the vector store.

    Args:
        vs: The vector store.
        rcfg: The retriever configuration.

    Returns:
        The retriever instance.
    """
    kw = {"k": rcfg.get("k", 4)}
    expr = rcfg.get("expr", "")
    if expr: kw["expr"] = expr
    return vs.as_retriever(search_kwargs=kw)

def create_or_update(vs, docs: List[Document]):
    """
    Upserts documents into the vector store with explicit IDs.

    Args:
        vs: The vector store.
        docs: The documents to upsert.
    """
    if not docs:
        return

    texts = [d.page_content for d in docs]
    metadatas = [d.metadata for d in docs]

    # Build stable IDs if we have a chunk_id; otherwise fall back to UUID
    ids = []
    for d in docs:
        cid = d.metadata.get("chunk_id")
        if cid is None:
            cid = str(uuid4())
        ids.append(f"chunk-{cid}")

    # Insert with explicit IDs (required when auto_id=False)
    vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)
