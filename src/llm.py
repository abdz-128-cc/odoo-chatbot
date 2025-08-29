from __future__ import annotations
import os, json
import google.generativeai as genai
from typing import Optional

class GeminiClient:
    def __init__(self, model: str, temperature: float=0.0, max_output_tokens: int=2048,
                 top_p: float=1.0, top_k: int=40, system_instruction: Optional[str]=None):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set")
        genai.configure(api_key=api_key)
        self.model_name = model
        self.generation_config = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_output_tokens": max_output_tokens,
        }
        self.system_instruction = system_instruction

    def _model(self, system_instruction: Optional[str]=None):
        return genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            system_instruction=system_instruction or self.system_instruction
        )

    def complete(self, prompt: str, system: Optional[str]=None) -> str:
        model = self._model(system)
        resp = model.generate_content([{"role":"user","parts":[prompt]}])
        return (resp.text or "").strip()

    def complete_json(self, prompt: str, system: Optional[str]=None) -> dict:
        text = self.complete(prompt, system=system)
        # try to locate JSON in the output robustly
        try:
            start = text.find("{"); end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start:end+1]
            return json.loads(text)
        except Exception:
            return {"route":"hr_policy", "confidence":0.0, "reason":"parse_error", "raw": text}
