from __future__ import annotations
from typing import List
from langchain_core.documents import Document
from .prompts import render_prompt

def format_context(docs: List[Document]) -> str:
    """
    Formats document contexts with source and page information.

    Args:
        docs: The list of documents.

    Returns:
        The formatted context string.
    """
    lines = []
    for i, d in enumerate(docs):
        page = d.metadata.get("page", "N/A")
        source_info = f"Source [{i}] (Page: {page})"
        lines.append(f"{source_info}\n{d.page_content}")
    return "\n\n".join(lines)

def prepare_rag_prompt(chain_prompt: str, question: str, role: str,
                       docs: list, admin_roles: list[str], memory=None) -> str:
    """
    Prepares the full prompt for the RAG chain, including context and history.

    Args:
        chain_prompt: The chain prompt template.
        question: The user's question.
        role: The user's role.
        docs: The retrieved documents.
        admin_roles: List of admin roles.
        memory: Optional conversation memory.

    Returns:
        The prepared prompt string.
    """
    ctx = format_context(docs) if docs else ""
    history_text = ""
    if memory:
        hist = memory.load_memory_variables({}).get("history", [])
        if hist:
            history_text = "\n".join([f"{m.type}: {m.content}" for m in hist])

    prompt_context = f"Conversation so far:\n{history_text}\n\n" if history_text else ""

    return prompt_context + render_prompt(
        chain_prompt,
        question=question,
        role=role,
        context=ctx,
        admin_roles=admin_roles
    )

def answer_with_chain(llm, chain_prompt: str, question: str, role: str,
                      docs: list, admin_roles: list[str], memory=None):
    """
    Generates an answer using the RAG chain.

    Args:
        llm: The LLM client.
        chain_prompt: The chain prompt template.
        question: The user's question.
        role: The user's role.
        docs: The retrieved documents.
        admin_roles: List of admin roles.
        memory: Optional conversation memory.

    Returns:
        The generated answer.
    """
    prompt = prepare_rag_prompt(chain_prompt, question, role, docs, admin_roles, memory)
    answer = llm.complete(prompt)

    if memory:
        memory.chat_memory.add_user_message(question)
        memory.chat_memory.add_ai_message(answer)

    return answer