# src/embeddings.py
from __future__ import annotations
from langchain_huggingface import HuggingFaceEmbeddings
import torch

def build_embeddings(cfg: dict):
    # Auto-detect CUDA/CPU if "auto" is specified
    device = cfg.get("device", "cpu")
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    return HuggingFaceEmbeddings(
        model_name=cfg["model"],
        model_kwargs={"device": device},
        encode_kwargs={
            "normalize_embeddings": cfg.get("normalize_embeddings", True),
            "batch_size": cfg.get("batch_size", 64),
            "convert_to_numpy": True,
        },
    )
