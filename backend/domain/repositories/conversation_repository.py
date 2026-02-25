"""对话仓储接口"""
from abc import ABC, abstractmethod
from typing import Optional
from backend.domain.entities.conversation import Conversation


class IConversationRepository(ABC):
    """对话仓储接口"""
    
    @abstractmethod
    async def save(self, conversation: Conversation) -> Conversation:
        """保存对话"""
        pass
    
    @abstractmethod
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """根据ID获取对话"""
        pass
    
    @abstractmethod
    async def delete(self, conversation_id: str) -> bool:
        """删除对话"""
        pass

