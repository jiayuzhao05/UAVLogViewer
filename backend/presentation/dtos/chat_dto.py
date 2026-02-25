"""DTOs for chat flows"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """Chat request DTO"""
    question: str = Field(..., description="User question")
    conversation_id: Optional[str] = Field(None, description="Conversation ID (optional for continuing)")
    file_id: Optional[str] = Field(None, description="File ID (optional to bind flight log)")


class ChatResponse(BaseModel):
    """Chat response DTO"""
    answer: str = Field(..., description="Answer")
    conversation_id: str = Field(..., description="Conversation ID")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    sources: List[str] = Field(default_factory=list, description="Data sources")
    requires_clarification: bool = Field(False, description="Whether clarification is needed")
    clarification_question: Optional[str] = Field(None, description="Clarification question")


class FileUploadResponse(BaseModel):
    """File upload response DTO"""
    file_id: str = Field(..., description="File ID")
    filename: str = Field(..., description="Filename")
    message: str = Field(..., description="Upload result message")
    parsed_messages: int = Field(0, description="Total parsed messages")

