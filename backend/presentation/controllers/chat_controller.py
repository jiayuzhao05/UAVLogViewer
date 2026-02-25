"""Chat controller"""
from fastapi import UploadFile, File
from typing import Optional
import uuid
import os
import aiofiles
from datetime import datetime
from backend.presentation.dtos.chat_dto import ChatRequest, ChatResponse, FileUploadResponse
from backend.application.services.chat_service import ChatService
from backend.application.services.telemetry_service import TelemetryService
from backend.application.services.anomaly_service import AnomalyService
from backend.domain.entities.flight_log import FlightLog
from backend.domain.repositories.flight_log_repository import IFlightLogRepository
from backend.infrastructure.parsers.mavlink_parser import MAVLinkParser


class ChatController:
    """Chat Controller - Handles HTTP requests"""
    
    def __init__(
        self,
        chat_service: ChatService,
        telemetry_service: TelemetryService,
        flight_log_repository: IFlightLogRepository,
        anomaly_service: AnomalyService,
    ):
        self.chat_service = chat_service
        self.telemetry_service = telemetry_service
        self.flight_log_repository = flight_log_repository
        self.anomaly_service = anomaly_service
        self.parser = MAVLinkParser()
        self.upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        handle chat request
        
        Args:
            request: chat request
            
        Returns:
            chat response
        """
        result = await self.chat_service.ask_question(
            question=request.question,
            conversation_id=request.conversation_id,
            file_id=request.file_id,
        )
        
        return ChatResponse(
            answer=result.answer,
            conversation_id=result.conversation_id,
            confidence=result.confidence,
            sources=result.sources,
            requires_clarification=result.requires_clarification,
            clarification_question=result.clarification_question,
        )
    
    async def upload_file(self, file: UploadFile = File(...)) -> FileUploadResponse:
        """
        uplaod .bin document
        
        Args:
            file: updated file
            
        Returns:
            upload response
        """
        # verify file type
        if not file.filename.endswith('.bin'):
            return FileUploadResponse(
                file_id="",
                filename=file.filename or "",
                message="only support.bin file",
            )
        
        # generate file ID
        file_id = str(uuid.uuid4())
        file_path = os.path.join(self.upload_dir, f"{file_id}.bin")
        
        # save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Parse file
        try:
            parsed_data = self.parser.parse(file_path)
            parsed_messages = parsed_data.get("metadata", {}).get(
                "total_messages", len(parsed_data.get("messages", []))
            )
            
            # Create FlightLog entity
            flight_log = FlightLog(
                file_id=file_id,
                filename=file.filename or "unknown.bin",
                upload_time=datetime.now(),
                parsed_data=parsed_data,
                metadata={
                    "file_size": len(content),
                    "content_type": file.content_type,
                },
            )
            
            # Save to repository
            await self.flight_log_repository.save(flight_log)
            # Invalidate caches
            self.telemetry_service.invalidate_cache(file_id)
            self.anomaly_service.invalidate(file_id)
            
            # Delete temporary file (do not persist to disk)
            os.remove(file_path)
            
            return FileUploadResponse(
                file_id=file_id,
                filename=file.filename or "",
                message=(
                    "The file has been uploaded successfully and "
                    f"parsed {parsed_messages} messages"
                ),
                parsed_messages=parsed_messages,
            )
        except Exception as e:
            # Clean up file on failure
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return FileUploadResponse(
                file_id="",
                filename=file.filename or "",
                message=f"File parsing failed: {str(e)}",
            )

