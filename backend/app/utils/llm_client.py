"""
Gemini API wrapper for structured output generation.
"""
import json
import google.generativeai as genai
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
import logging

from ..config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Client for interacting with Gemini AI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM client."""
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = settings.gemini_model
        self.max_retries = settings.max_retries
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
        
        self._model = None
    
    @property
    def model(self):
        """Get or create the generative model."""
        if self._model is None:
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "top_p": 0.95,
                    "top_k": 40,
                }
            )
        return self._model
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        context: Optional[str] = None
    ) -> T:
        """
        Generate a structured response using Gemini.
        
        Args:
            prompt: The instruction prompt
            response_model: Pydantic model for the expected response
            context: Optional additional context
        
        Returns:
            Parsed response as the specified Pydantic model
        """
        # Build the full prompt with JSON schema
        schema = response_model.model_json_schema()
        full_prompt = self._build_prompt(prompt, schema, context)
        
        for attempt in range(self.max_retries):
            try:
                response = await self._generate(full_prompt)
                parsed = self._parse_response(response, response_model)
                return parsed
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
        
        raise RuntimeError("Failed to generate structured response")
    
    async def _generate(self, prompt: str) -> str:
        """Generate raw text response from Gemini."""
        response = await self.model.generate_content_async(prompt)
        return response.text
    
    def _build_prompt(
        self,
        instruction: str,
        schema: dict,
        context: Optional[str] = None
    ) -> str:
        """Build a prompt requesting JSON output."""
        prompt_parts = [
            "You are an expert CV/resume analyzer and writer.",
            "",
            "INSTRUCTION:",
            instruction,
        ]
        
        if context:
            prompt_parts.extend([
                "",
                "CONTEXT:",
                context,
            ])
        
        prompt_parts.extend([
            "",
            "OUTPUT FORMAT:",
            "You must respond with valid JSON matching this schema:",
            "```json",
            json.dumps(schema, indent=2),
            "```",
            "",
            "Respond ONLY with the JSON object, no additional text.",
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response: str, model: Type[T]) -> T:
        """Parse JSON response into Pydantic model."""
        # Clean up response - remove markdown code blocks if present
        text = response.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Parse JSON
        data = json.loads(text)
        
        # Validate with Pydantic
        return model.model_validate(data)
    
    async def generate_text(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate free-form text response."""
        full_prompt = prompt
        if context:
            full_prompt = f"{prompt}\n\nContext:\n{context}"
        
        return await self._generate(full_prompt)


# Global client instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get the global LLM client instance."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


def set_llm_api_key(api_key: str):
    """Set API key for the LLM client."""
    global _client
    _client = LLMClient(api_key=api_key)
