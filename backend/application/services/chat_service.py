"""Chat service - application layer"""
from typing import Optional
from backend.domain.value_objects.query import Query, QueryResult
from backend.application.use_cases.chat_use_case import ChatUseCase


class ChatService:
    """Chat service encapsulating chat-related business logic"""
    
    def __init__(self, chat_use_case: ChatUseCase):
        self.chat_use_case = chat_use_case
    
    async def ask_question(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> QueryResult:
        """
        Handle a user question.
        
        Args:
            question: user question
            conversation_id: conversation ID (optional, for continuing a thread)
            file_id: file ID (optional, to bind a flight log)
            
        Returns:
            query result
        """
        query = Query(
            text=question,
            conversation_id=conversation_id,
            file_id=file_id,
        )
        
        return await self.chat_use_case.process_query(query)

