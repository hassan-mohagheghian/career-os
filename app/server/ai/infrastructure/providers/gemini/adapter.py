"""Gemini API provider.

SRP: Handles Google Gemini API communication via LangChain.
"""

from __future__ import annotations

import os
from typing import Optional

from ..base import LLMProvider, ProviderConfig, ProviderResponse


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini API."""

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig(name="gemini"))
        self._llm = None

    def _ensure_llm(self):
        if self._llm is None:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                
                # Get API key from config or environment variable
                api_key = self._config.api_key or os.environ.get("GOOGLE_API_KEY")
                if not api_key:
                    raise RuntimeError("Gemini provider requires GOOGLE_API_KEY.")

                self._llm = ChatGoogleGenerativeAI(
                    model=self._config.model or "gemini-2.0-flash",
                    google_api_key=api_key,
                    temperature=self._config.temperature,
                    max_tokens=self._config.max_tokens,
                )
            except ImportError:
                raise RuntimeError(
                    "Gemini provider requires 'langchain-google-genai' package."
                )

    def generate(
        self,
        prompt: str,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        self._ensure_llm()
        
        # Simple invocation for non-structured text
        response = self._llm.invoke(prompt)
        
        return ProviderResponse(
            content=response.content,
            metadata={"model": self._config.model or "gemini-2.0-flash"},
            provider="gemini",
            model=self._config.model or "gemini-2.0-flash",
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Optional[dict] = None,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        self._ensure_llm()
        
        # For structured output with Gemini, we can use with_structured_output
        if schema:
            llm_with_structure = self._llm.with_structured_output(schema)
            response = llm_with_structure.invoke(prompt)
            # Response is already the structured object (dict/model)
            import json
            return ProviderResponse(
                content=json.dumps(response),
                metadata={"model": self._config.model or "gemini-2.0-flash"},
                provider="gemini",
                model=self._config.model or "gemini-2.0-flash",
            )
        
        return self.generate(prompt, context, timeout)
