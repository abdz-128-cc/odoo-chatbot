from __future__ import annotations
import os
from typing import Optional, Dict, Any, Iterable
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


# Pydantic model for robust JSON parsing of router output
class Route(BaseModel):
    route: str = Field(description="The route to take, must be 'onboarding' or 'hr_policy'")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    reason: str = Field(description="A brief reason for the choice")


class OpenAIClient:
    """A wrapper around LangChain's ChatOpenAI to fit the application's existing interface."""

    def __init__(self, model: str, temperature: float = 0.0, max_output_tokens: int = 2048):
        """
        Initializes the OpenAI client wrapper.

        Args:
            model: The OpenAI model name.
            temperature: The sampling temperature (default 0.0).
            max_output_tokens: The maximum output tokens (default 2048).

        Raises:
            RuntimeError: If OPENAI_API_KEY is not set.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in the environment.")
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_output_tokens,
            api_key=api_key
        )

    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Generates a text completion using the LLM.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.

        Returns:
            The generated response content.
        """
        messages = []
        if system:
            messages.append(("system", system))
        messages.append(("human", prompt))
        response = self.llm.invoke(messages)
        return response.content.strip()

    def stream(self, prompt: str, system: Optional[str] = None) -> Iterable[str]:
        """
        Streams the LLM response chunk by chunk.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.

        Yields:
            Content chunks from the LLM stream.
        """
        messages = []
        if system:
            messages.append(("system", system))
        messages.append(("human", prompt))

        for chunk in self.llm.stream(messages):
            yield chunk.content

    def complete_json(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates a JSON response with parsing.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.

        Returns:
            The parsed JSON dictionary or error structure on failure.
        """
        parser = JsonOutputParser(pydantic_object=Route)

        prompt_with_format_instructions = f"{prompt}\n\n{parser.get_format_instructions()}"

        messages = []
        if system:
            messages.append(("system", system))
        messages.append(("human", prompt_with_format_instructions))

        chain = self.llm | parser

        try:
            result = chain.invoke(messages)
            return result
        except Exception as e:
            raw_text = self.llm.invoke(messages).content
            return {
                "route": "hr_policy",
                "confidence": 0.0,
                "reason": f"JSON parsing error: {e}",
                "raw": raw_text
            }


def build_llm(cfg: Dict[str, Any]):
    """
    Builds an LLM client based on the configuration.

    Args:
        cfg: The LLM configuration dictionary.

    Returns:
        The LLM client instance.

    Raises:
        ValueError: If an unsupported provider is specified.
    """
    provider = cfg.get("provider", "openai").lower()

    if provider == "openai":
        return OpenAIClient(
            model=cfg["model"],
            temperature=cfg.get("temperature", 0.0),
            max_output_tokens=cfg.get("max_output_tokens", 2048),
        )
    else:
        raise ValueError(f"Unsupported LLM provider specified in config: '{provider}'")