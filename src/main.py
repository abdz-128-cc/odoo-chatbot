# src/main.py
from __future__ import annotations
from .config_loader import load_config
from .embeddings import build_embeddings
from .vectorstore import connect_milvus, get_vectorstore, make_retriever
from .llm import GeminiClient
from .router import choose_route
from .rag import answer_with_chain
from .reranker import build_reranker
from langchain.memory import ConversationBufferWindowMemory

# --- Globals for pre-loaded models and configs ---
# These will be initialized once at startup
_APP_CONFIG = None
_LLM_CLIENT = None
_EMBEDDINGS = None
_VECTOR_STORE = None
_RERANKER = None
_MEMORIES = {}  # Session memory remains dynamic


def initialize_models():
    """
    This function is called once at application startup.
    It loads all the heavy models and components into memory.
    """
    global _APP_CONFIG, _LLM_CLIENT, _EMBEDDINGS, _VECTOR_STORE, _RERANKER

    print("--- Initializing Models and Configuration ---")

    cfg = load_config()
    _APP_CONFIG = cfg["app"]

    # 1. Build and store LLM client
    llm_cfg = _APP_CONFIG["llm"]
    _LLM_CLIENT = GeminiClient(
        model=llm_cfg["model"],
        temperature=llm_cfg.get("temperature", 0.0),
        max_output_tokens=llm_cfg.get("max_output_tokens", 2048),
        top_p=llm_cfg.get("top_p", 1.0),
        top_k=llm_cfg.get("top_k", 40),
    )

    # 2. Build and store embeddings model
    _EMBEDDINGS = build_embeddings(_APP_CONFIG["embedding"])

    # 3. Connect to Milvus and build vector store
    connect_milvus(_APP_CONFIG["milvus"])
    _VECTOR_STORE = get_vectorstore(_EMBEDDINGS, _APP_CONFIG["milvus"])

    # 4. Build and store the reranker
    _RERANKER = build_reranker(_APP_CONFIG.get("reranker", {}), llm=_LLM_CLIENT)

    print("--- Models and Configuration Initialized Successfully ---")


def get_memory(user_id: str = "default"):
    mem_cfg = _APP_CONFIG.get("memory", {})
    if mem_cfg.get("type") == "conversation_buffer_window":
        if user_id not in _MEMORIES:
            _MEMORIES[user_id] = ConversationBufferWindowMemory(
                k=mem_cfg.get("k", 5),
                return_messages=True
            )
        return _MEMORIES[user_id]
    return None


def chat_once(question: str, role: str | None = None, user_id: str = "default"):
    """
    This function now uses the pre-loaded models for efficiency.
    """
    prompts = load_config()["prompts"]  # Prompts can be reloaded if they change
    role = role or _APP_CONFIG["roles"]["default_role"]

    # --- Use pre-loaded components ---
    rerank_cfg = _APP_CONFIG.get("reranker", {}) or {}
    candidates = int(rerank_cfg.get("candidates", _APP_CONFIG["retriever"].get("k", 4)))
    top_n = int(rerank_cfg.get("top_n", _APP_CONFIG["retriever"].get("k", 4)))

    retriever = make_retriever(_VECTOR_STORE, {**_APP_CONFIG["retriever"], "k": candidates})
    docs = retriever.invoke(question)

    if _RERANKER:
        docs = _RERANKER.rerank(question, docs, top_n=top_n)
    else:
        docs = docs[:_APP_CONFIG["retriever"].get("k", 4)]

    # route & chain
    route = choose_route(_LLM_CLIENT, prompts["router"], question, role)
    chain_key = "onboarding" if route == "onboarding" else "hr_policy"

    memory = get_memory(user_id)
    admin_roles = _APP_CONFIG["roles"]["admin_roles"]

    answer = answer_with_chain(_LLM_CLIENT, prompts[chain_key], question, role, docs, admin_roles, memory=memory)
    return route, answer