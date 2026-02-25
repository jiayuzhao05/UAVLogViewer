"""FastAPI main application"""
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (parent of backend/)
_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_env_path)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.presentation.controllers.chat_controller import ChatController
from backend.presentation.dtos.chat_dto import ChatRequest, ChatResponse, FileUploadResponse
from backend.infrastructure.storage.memory_repositories import (
    MemoryFlightLogRepository,
    MemoryConversationRepository,
)
from backend.infrastructure.llm.llm_factory import LLMFactory
from backend.application.services.telemetry_service import TelemetryService
from backend.application.services.chat_service import ChatService
from backend.application.use_cases.chat_use_case import ChatUseCase
from backend.application.services.anomaly_service import AnomalyService
from fastapi.staticfiles import StaticFiles


class DIContainer:
    """Dependency injection container"""
    
    def __init__(self):
        # Infrastructure layer
        self.flight_log_repository = MemoryFlightLogRepository()
        self.conversation_repository = MemoryConversationRepository()
        self.llm_client = LLMFactory.create_client()
        
        # Application layer
        self.telemetry_service = TelemetryService(self.flight_log_repository)
        self.anomaly_service = AnomalyService()
        self.chat_use_case = ChatUseCase(
            conversation_repository=self.conversation_repository,
            flight_log_repository=self.flight_log_repository,
            llm_client=self.llm_client,
            telemetry_service=self.telemetry_service,
            anomaly_service=self.anomaly_service,
        )
        self.chat_service = ChatService(self.chat_use_case)
        
        # Presentation layer
        self.chat_controller = ChatController(
            chat_service=self.chat_service,
            telemetry_service=self.telemetry_service,
            flight_log_repository=self.flight_log_repository,
            anomaly_service=self.anomaly_service,
        )


# Global DI container
container = DIContainer()


# FastAPI application
app = FastAPI(
    title="UAV Logger Chatbot API",
    description="MAVLink telemetry analysis chatbot",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, limit to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static UI (lightweight demo UI)
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="ui")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "UAV Logger Chatbot API",
        "version": "1.0.0",
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint
    
    Handles user questions about MAVLink telemetry data
    """
    return await container.chat_controller.chat(request)


@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload .bin file
    
    Upload and parse MAVLink flight log file
    """
    return await container.chat_controller.upload_file(file)


@app.get("/api/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.get("/api/telemetry/summary/{file_id}")
async def telemetry_summary(file_id: str):
    """Return telemetry and anomaly summaries for a given file."""
    summary = await container.telemetry_service.get_flight_summary(file_id)
    if not summary:
        raise HTTPException(status_code=404, detail="File not found")
    telemetry = await container.telemetry_service.query_telemetry(file_id)
    anomaly = container.anomaly_service.summarize_anomalies_cached(file_id, telemetry)
    return {"summary": summary, "anomaly_summary": anomaly}


if __name__ == "__main__":
    import uvicorn
    # Dev env uses 0.0.0.0; in production prefer 127.0.0.1 or a specific bind
    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: B104

