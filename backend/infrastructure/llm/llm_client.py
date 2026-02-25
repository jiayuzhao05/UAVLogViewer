"""LLM client interface"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class ILLMClient(ABC):
    """LLM client interface supporting multiple providers"""
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Send a chat request.
        
        Args:
            messages: list of messages, e.g. [{"role": "user", "content": "..."}]
            system_prompt: optional system prompt
            temperature: sampling temperature
            
        Returns:
            response text from the LLM
        """
        pass
    
    @abstractmethod
    async def chat_with_context(
        self,
        messages: List[Dict[str, str]],
        context: Dict,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Send a chat request with additional context.
        
        Args:
            messages: list of messages
            context: context payload (e.g., telemetry summary)
            system_prompt: optional system prompt
            
        Returns:
            response text from the LLM
        """
        pass

