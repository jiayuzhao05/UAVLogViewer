"""conversation entity"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class Message:
    """information entity"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """transfer to dict"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Conversation:
    """Conversation Entity - Maintains the status of the conversation"""
    conversation_id: str
    file_id: Optional[str] = None  # the associated flight log file ID
    messages: List[Message] = field(default_factory=list)
    context: Dict = field(default_factory=dict)  # Dialogue context information
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, message: Message):
        """add message"""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_messages_for_llm(self) -> List[Dict]:
        """Get the message format for LLMs"""
        return [msg.to_dict() for msg in self.messages]
    
    def get_context_summary(self) -> Dict:
        """Get the context summary"""
        return {
            "conversation_id": self.conversation_id,
            "file_id": self.file_id,
            "message_count": len(self.messages),
            "has_file": self.file_id is not None,
        }

