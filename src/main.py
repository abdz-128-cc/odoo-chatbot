# src/main.py
from __future__ import annotations
from .config_loader import load_config
from .embeddings import build_embeddings
from .vectorstore import connect_milvus, get_vectorstore, make_retriever
from .llm import build_llm
from .router import choose_route
from .rag import answer_with_chain, prepare_rag_prompt
from .reranker import build_reranker
from langchain.memory import ConversationBufferWindowMemory

# --- Globals for pre-loaded models and configs ---
_APP_CONFIG = None
_PROMPTS_CONFIG = None
_LLM_CLIENT = None
_EMBEDDINGS = None
_VECTOR_STORE = None
_RERANKER = None
_MEMORIES = {}

def initialize_models():
    """
    This function is called once at application startup.
    It loads all the heavy models and components into memory.
    """
    global _APP_CONFIG, _PROMPTS_CONFIG, _LLM_CLIENT, _EMBEDDINGS, _VECTOR_STORE, _RERANKER

    print("--- Initializing Models and Configuration ---")

    cfg = load_config()
    _APP_CONFIG = cfg["app"]
    _PROMPTS_CONFIG = cfg["prompts"]

    llm_cfg = _APP_CONFIG["llm"]
    _LLM_CLIENT = build_llm(llm_cfg)
    _EMBEDDINGS = build_embeddings(_APP_CONFIG["embedding"])
    connect_milvus(_APP_CONFIG["milvus"])
    _VECTOR_STORE = get_vectorstore(_EMBEDDINGS, _APP_CONFIG["milvus"])
    _RERANKER = build_reranker(_APP_CONFIG.get("reranker", {}), llm=_LLM_CLIENT)

    print("--- Models and Configuration Initialized Successfully ---")

def get_prompts_config():
    """Safely retrieves the prompts configuration after initialization."""
    if _PROMPTS_CONFIG is None:
        raise RuntimeError("Prompts configuration has not been initialized.")
    return _PROMPTS_CONFIG

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


def chat_stream(question: str, role: str | None = None, user_id: str = "default"):
    """
    A generator function that streams the RAG response.
    It yields events for the route and then for each token chunk.
    """
    # --- 1. Synchronous Setup (Retrieval, Reranking, Routing) ---
    prompts = get_prompts_config()
    role = role or _APP_CONFIG["roles"]["default_role"]

    rerank_cfg = _APP_CONFIG.get("reranker", {}) or {}
    candidates = int(rerank_cfg.get("candidates", _APP_CONFIG["retriever"].get("k", 4)))
    retriever = make_retriever(_VECTOR_STORE, {**_APP_CONFIG["retriever"], "k": candidates})
    docs = retriever.invoke(question)

    if _RERANKER:
        top_n = int(rerank_cfg.get("top_n", _APP_CONFIG["retriever"].get("k", 4)))
        docs = _RERANKER.rerank(question, docs, top_n=top_n)
    else:
        docs = docs[:_APP_CONFIG["retriever"].get("k", 4)]

    route = choose_route(_LLM_CLIENT, prompts["router"], question, role)
    yield {"type": "route", "data": route}

    # --- 2. Prepare Prompt and Memory ---
    chain_key = "onboarding" if route == "onboarding" else "hr_policy"
    memory = get_memory(user_id)
    admin_roles = _APP_CONFIG["roles"]["admin_roles"]

    final_prompt = prepare_rag_prompt(
        prompts[chain_key], question, role, docs, admin_roles, memory=memory
    )

    # --- 3. Stream the LLM Response ---
    full_response = []
    for chunk in _LLM_CLIENT.stream(final_prompt):
        full_response.append(chunk)
        yield {"type": "chunk", "data": chunk}

    # --- 4. Update Memory (After Stream is Complete) ---
    if memory:
        memory.chat_memory.add_user_message(question)
        memory.chat_memory.add_ai_message("".join(full_response))


def chat_once(question: str, role: str | None = None, user_id: str = "default"):
    """
    This function now uses the pre-loaded models for efficiency.
    """
    prompts = get_prompts_config() # Use the getter here as well for consistency
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