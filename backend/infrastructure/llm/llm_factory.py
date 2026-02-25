"""LLM client factory"""
import os
from typing import Optional
from backend.infrastructure.llm.llm_client import ILLMClient
from backend.infrastructure.llm.openai_client import OpenAIClient
from backend.infrastructure.llm.anthropic_client import AnthropicClient


class LLMFactory:
    """Factory for creating LLM clients based on configuration"""
    
    @staticmethod
    def create_client(provider: Optional[str] = None) -> ILLMClient:
        """
        Create an LLM client.
        
        Args:
            provider: LLM provider ("openai" or "anthropic"); auto-detects when None
            
        Returns:
            LLM client instance
        """
        provider = provider or os.getenv("LLM_PROVIDER", "openai").lower()
        
        if provider == "openai":
            return OpenAIClient()
        elif provider == "anthropic":
            return AnthropicClient()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

