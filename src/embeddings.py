from __future__ import annotations
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
import torch

def build_embeddings(cfg: dict):
    """
    Builds an embeddings model based on the configuration.

    Args:
        cfg: The configuration dictionary for embeddings.

    Returns:
        The embeddings model instance.

    Raises:
        ValueError: If an unsupported provider is specified.
    """
    provider = cfg.get("provider", "openai").lower()

    if provider == "openai":
        return OpenAIEmbeddings(model=cfg["model"])

    elif provider == "huggingface":
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
    else:
        raise ValueError(f"Unsupported embeddings provider specified in config: '{provider}'")
