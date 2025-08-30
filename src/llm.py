from __future__ import annotations
import os
from typing import Optional, Dict, Any
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
        """Generates a standard text completion."""
        messages = []
        if system:
            messages.append(("system", system))
        messages.append(("human", prompt))
        response = self.llm.invoke(messages)
        return response.content.strip()

    def stream(self, prompt: str, system: Optional[str] = None) -> Iterable[str]:
        """Streams the response from the LLM, yielding content chunks."""
        messages = []
        if system:
            messages.append(("system", system))
        messages.append(("human", prompt))

        for chunk in self.llm.stream(messages):
            yield chunk.content

    def complete_json(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """Generates a JSON response, with robust parsing and a fallback mechanism."""
        parser = JsonOutputParser(pydantic_object=Route)

        # Combine the user prompt with formatting instructions from the parser
        prompt_with_format_instructions = f"{prompt}\n\n{parser.get_format_instructions()}"

        messages = []
        if system:
            messages.append(("system", system))
        messages.append(("human", prompt_with_format_instructions))

        # Create a chain that pipes the LLM output to the JSON parser
        chain = self.llm | parser

        try:
            result = chain.invoke(messages)
            return result
        except Exception as e:
            # If JSON parsing fails, return a default error structure
            raw_text = self.llm.invoke(messages).content
            return {
                "route": "hr_policy",
                "confidence": 0.0,
                "reason": f"JSON parsing error: {e}",
                "raw": raw_text
            }


def build_llm(cfg: Dict[str, Any]):
    """Factory function to build the appropriate LLM client based on config."""
    provider = cfg.get("provider", "openai").lower()

    if provider == "openai":
        return OpenAIClient(
            model=cfg["model"],
            temperature=cfg.get("temperature", 0.0),
            max_output_tokens=cfg.get("max_output_tokens", 2048),
        )
    else:
        raise ValueError(f"Unsupported LLM provider specified in config: '{provider}'")