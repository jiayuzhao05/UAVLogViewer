"""Anthropic client implementation"""
import os
from typing import List, Dict, Optional
from anthropic import AsyncAnthropic
from backend.infrastructure.llm.llm_client import ILLMClient


class AnthropicClient(ILLMClient):
    """Anthropic client implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Send chat request."""
        # Convert to Anthropic API format
        anthropic_messages = []
        for msg in messages:
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=temperature,
            system=system_prompt or "",
            messages=anthropic_messages,
        )
        
        return response.content[0].text
    
    async def chat_with_context(
        self,
        messages: List[Dict[str, str]],
        context: Dict,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Send chat request with context."""
        enhanced_system_prompt = self._build_system_prompt(system_prompt, context)
        return await self.chat(messages, enhanced_system_prompt, temperature=0.7)
    
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

