"""In-memory storage implementations for repositories"""
from typing import Dict, Optional, List
from datetime import datetime
import uuid
from backend.domain.entities.flight_log import FlightLog
from backend.domain.entities.conversation import Conversation
from backend.domain.repositories.flight_log_repository import IFlightLogRepository
from backend.domain.repositories.conversation_repository import IConversationRepository


class MemoryFlightLogRepository(IFlightLogRepository):
    """In-memory flight log repository implementation"""
    
    def __init__(self):
        self._storage: Dict[str, FlightLog] = {}
        self._telemetry_data: Dict[str, List[Dict]] = {}
    
    async def save(self, flight_log: FlightLog) -> FlightLog:
        """Persist a flight log in memory."""
        self._storage[flight_log.file_id] = flight_log
        
        # Persist telemetry data
        if flight_log.parsed_data and "messages" in flight_log.parsed_data:
            self._telemetry_data[flight_log.file_id] = flight_log.parsed_data["messages"]
        
        return flight_log
    
    async def get_by_id(self, file_id: str) -> Optional[FlightLog]:
        """Get flight log by ID."""
        return self._storage.get(file_id)
    
    async def get_telemetry_data(
        self, 
        file_id: str, 
        message_type: Optional[str] = None
    ) -> List[Dict]:
        """Get telemetry data."""
        data = self._telemetry_data.get(file_id, [])
        
        if message_type:
            data = [msg for msg in data if msg.get("message_type") == message_type]
        
        return data
    
    async def delete(self, file_id: str) -> bool:
        """Delete flight log by ID."""
        if file_id in self._storage:
            del self._storage[file_id]
            if file_id in self._telemetry_data:
                del self._telemetry_data[file_id]
            return True
        return False


class MemoryConversationRepository(IConversationRepository):
    """In-memory conversation repository implementation"""
    
    def __init__(self):
        self._storage: Dict[str, Conversation] = {}
    
    async def save(self, conversation: Conversation) -> Conversation:
        """Persist a conversation."""
        self._storage[conversation.conversation_id] = conversation
        return conversation
    
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        return self._storage.get(conversation_id)
    
    async def delete(self, conversation_id: str) -> bool:
        """Delete conversation by ID."""
        if conversation_id in self._storage:
            del self._storage[conversation_id]
            return True
        return False
    
    async def create_new(self, file_id: Optional[str] = None) -> Conversation:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            conversation_id=conversation_id,
            file_id=file_id,
        )
        await self.save(conversation)
        return conversation

