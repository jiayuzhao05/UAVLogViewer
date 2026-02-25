"""OpenAI client implementation"""
import os
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from backend.infrastructure.llm.llm_client import ILLMClient


class OpenAIClient(ILLMClient):
    """OpenAI client implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Send chat completion request."""
        chat_messages = []
        
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        
        chat_messages.extend(messages)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=chat_messages,
            temperature=temperature,
        )
        
        return response.choices[0].message.content
    
    async def chat_with_context(
        self,
        messages: List[Dict[str, str]],
        context: Dict,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Send chat request with additional context."""
        # Build system prompt including context
        enhanced_system_prompt = self._build_system_prompt(system_prompt, context)
        return await self.chat(messages, enhanced_system_prompt)
    
    def _build_system_prompt(self, base_prompt: Optional[str], context: Dict) -> str:
        """Build system prompt that includes context."""
        prompt_parts = []
        
        if base_prompt:
            prompt_parts.append(base_prompt)
        
        # Add MAVLink docs link
        prompt_parts.append(
            "\nReference: https://ardupilot.org/plane/docs/logmessages.html"
        )
        
        # Add telemetry summary context
        if context.get("telemetry_summary"):
            summary = context["telemetry_summary"]
            prompt_parts.append(f"\nCurrent flight log info:")
            prompt_parts.append(f"- Filename: {summary.get('filename', 'N/A')}")
            prompt_parts.append(f"- Total messages: {summary.get('total_messages', 0)}")
            if summary.get("message_types"):
                prompt_parts.append(f"- Message types: {', '.join(summary['message_types'])}")
            if summary.get("time_range"):
                tr = summary["time_range"]
                prompt_parts.append(f"- Time range: {tr.get('start', 0)} - {tr.get('end', 0)}")
                prompt_parts.append(f"- Duration: {tr.get('duration', 0)} seconds")
        
        prompt_parts.append(
            "\nAnswer based on telemetry data and retrieve relevant details."
            "If information is insufficient, proactively ask the user for more context."
        )
        
        return "\n".join(prompt_parts)

