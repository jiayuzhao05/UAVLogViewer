"""Query value objects"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class Query:
    """User query value object"""
    text: str
    conversation_id: Optional[str] = None
    file_id: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Validate query content."""
        return bool(self.text and self.text.strip())


@dataclass(frozen=True)
class QueryResult:
    """Query result value object"""
    answer: str
    conversation_id: str  # Conversation ID
    confidence: float  # 0.0 to 1.0
    sources: List[str] = None  # Data sources
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    
    def __post_init__(self):
        if self.sources is None:
            object.__setattr__(self, 'sources', [])

