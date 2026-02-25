"""Chat use case"""
from typing import Optional, Dict, List
from backend.domain.value_objects.query import Query, QueryResult
from backend.domain.entities.conversation import Conversation, Message
from backend.domain.repositories.conversation_repository import IConversationRepository
from backend.domain.repositories.flight_log_repository import IFlightLogRepository
from backend.infrastructure.llm.llm_client import ILLMClient
from backend.application.services.telemetry_service import TelemetryService
from backend.application.services.anomaly_service import AnomalyService


class ChatUseCase:
    """Chat use case - core logic for handling user queries"""
    
    def __init__(
        self,
        conversation_repository: IConversationRepository,
        flight_log_repository: IFlightLogRepository,
        llm_client: ILLMClient,
        telemetry_service: TelemetryService,
        anomaly_service: AnomalyService,
    ):
        self.conversation_repository = conversation_repository
        self.flight_log_repository = flight_log_repository
        self.llm_client = llm_client
        self.telemetry_service = telemetry_service
        self.anomaly_service = anomaly_service
    
    async def process_query(self, query: Query) -> QueryResult:
        """
        Handle a user query.
        
        Args:
            query: user query
            
        Returns:
            query result
        """
        # Validate query
        if not query.is_valid():
            # Create a temporary conversation ID for the error response
            import uuid
            return QueryResult(
                answer="Please enter a valid question.",
                conversation_id=str(uuid.uuid4()),
                confidence=0.0,
                requires_clarification=False,
            )
        
        # Get or create conversation
        conversation = await self._get_or_create_conversation(query)
        
        # Append user message
        user_message = Message(role="user", content=query.text)
        conversation.add_message(user_message)
        
        # Build context
        context = await self._build_context(conversation)
        
        # Retrieve relevant telemetry data
        telemetry_data = await self._retrieve_telemetry_data(conversation, query)
        
        # Call LLM to generate answer
        answer = await self._generate_answer(
            conversation,
            context,
            telemetry_data,
        )
        
        # Append assistant message
        assistant_message = Message(role="assistant", content=answer)
        conversation.add_message(assistant_message)
        
        # Persist conversation
        await self.conversation_repository.save(conversation)
        
        # Decide if clarification is needed
        requires_clarification = self._needs_clarification(answer)
        clarification_question = None
        if requires_clarification:
            clarification_question = self._extract_clarification_question(answer)
        
        return QueryResult(
            answer=answer,
            conversation_id=conversation.conversation_id,
            confidence=0.8 if not requires_clarification else 0.5,
            sources=[f"Flight log: {conversation.file_id}"] if conversation.file_id else [],
            requires_clarification=requires_clarification,
            clarification_question=clarification_question,
        )
    
    async def _get_or_create_conversation(self, query: Query) -> Conversation:
        """Get existing conversation or create a new one."""
        if query.conversation_id:
            conversation = await self.conversation_repository.get_by_id(query.conversation_id)
            if conversation:
                return conversation
        
        # Create new conversation
        file_id = query.file_id
        if hasattr(self.conversation_repository, 'create_new'):
            return await self.conversation_repository.create_new(file_id)
        else:
            import uuid
            conversation = Conversation(
                conversation_id=str(uuid.uuid4()),
                file_id=file_id,
            )
            return await self.conversation_repository.save(conversation)
    
    async def _build_context(self, conversation: Conversation) -> Dict:
        """Build conversation context."""
        context = {
            "conversation_id": conversation.conversation_id,
            "file_id": conversation.file_id,
        }
        
        # If linked to a flight log, add summary
        if conversation.file_id:
            summary = await self.telemetry_service.get_flight_summary(conversation.file_id)
            context["telemetry_summary"] = summary
            # Attach anomaly summary for richer reasoning (cached)
            telemetry = await self.telemetry_service.query_telemetry(conversation.file_id)
            context["anomaly_summary"] = self.anomaly_service.summarize_anomalies_cached(
                conversation.file_id, telemetry
            )
        
        return context
    
    async def _retrieve_telemetry_data(
        self,
        conversation: Conversation,
        query: Query,
    ) -> List[Dict]:
        """Retrieve related telemetry data."""
        if not conversation.file_id:
            return []
        
        # Infer message types to fetch based on query text
        message_types = self._infer_message_types(query.text)
        
        telemetry_data = []
        for msg_type in message_types:
            data = await self.telemetry_service.query_telemetry(
                conversation.file_id,
                message_type=msg_type,
            )
            telemetry_data.extend(data)
        
        # If no specific type matched, fetch all data
        if not telemetry_data:
            telemetry_data = await self.telemetry_service.query_telemetry(
                conversation.file_id,
            )
        
        # Limit volume to avoid overlong context
        return telemetry_data[:1000]  # Return at most 1000 messages
    
    def _infer_message_types(self, query_text: str) -> List[str]:
        """Infer message types needed based on query text."""
        query_lower = query_text.lower()
        message_types = []
        
        if any(word in query_lower for word in ["altitude", "alt"]):
            message_types.extend(["GPS_RAW_INT", "GLOBAL_POSITION_INT"])
        
        if any(word in query_lower for word in ["battery", "temp", "temperature"]):
            message_types.append("BATTERY_STATUS")
        
        if any(word in query_lower for word in ["gps", "signal"]):
            message_types.append("GPS_RAW_INT")
        
        if any(word in query_lower for word in ["rc", "remote"]):
            message_types.append("RC_CHANNELS")
        
        if any(word in query_lower for word in ["error", "critical"]):
            message_types.append("STATUSTEXT")
        
        return list(set(message_types))  # Deduplicate
    
    async def _generate_answer(
        self,
        conversation: Conversation,
        context: Dict,
        telemetry_data: List[Dict],
    ) -> str:
        """Generate answer."""
        # Build system prompt
        system_prompt = self._build_system_prompt(telemetry_data)
        
        # Get conversation history
        messages = conversation.get_messages_for_llm()
        
        # Call LLM
        answer = await self.llm_client.chat_with_context(
            messages=messages,
            context=context,
            system_prompt=system_prompt,
        )
        
        return answer
    
    def _build_system_prompt(self, telemetry_data: List[Dict]) -> str:
        """Build system prompt."""
        prompt = """You are a professional MAVLink telemetry analysis assistant.
Your task is to help users analyze flight log data and answer questions about flight parameters, states, and events.

Guidelines:
1. Base answers on the provided telemetry data and keep them accurate.
2. If data is insufficient, proactively ask the user for more information.
3. Use professional terminology but keep answers easy to understand.
4. If anomalies or errors are detected, clearly call them out.

Reference: https://ardupilot.org/plane/docs/logmessages.html
"""
        
        # Add telemetry snippets when available
        if telemetry_data:
            # Extract a small sample for context
            sample_data = telemetry_data[:10]  # Sample first 10 messages
            prompt += f"\nSample telemetry available (total {len(telemetry_data)} messages):\n"
            for msg in sample_data:
                prompt += f"- {msg.get('message_type', 'UNKNOWN')}: {msg.get('data', {})}\n"

        # Encourage anomaly reasoning with provided summaries and hints
        prompt += """

Use the provided telemetry summary and anomaly summary to:
- Look for sudden changes in altitude, battery temperature, or inconsistent GPS fix.
- Cross-check high-severity STATUSTEXT messages and RC signal quality issues.
- If evidence is insufficient, ask clarifying questions instead of guessing.
"""
        
        return prompt
    
    def _needs_clarification(self, answer: str) -> bool:
        """Determine whether the answer needs clarification."""
        clarification_keywords = [
            "need more information",
            "please provide",
            "could you clarify",
            "not sure",
        ]
        answer_lower = answer.lower()
        return any(keyword in answer_lower for keyword in clarification_keywords)
    
    def _extract_clarification_question(self, answer: str) -> Optional[str]:
        """Extract a clarification question from the answer if present."""
        # Simple approach: return the first sentence containing a question mark
        for sentence in answer.split("."):
            if "?" in sentence:
                return sentence.strip()
        return None

