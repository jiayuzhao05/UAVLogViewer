"""Flight log entities"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class FlightLog:
    """Flight log entity"""
    file_id: str
    filename: str
    upload_time: datetime
    parsed_data: Dict  # Parsed MAVLink data
    metadata: Dict  # Metadata (file size, format, etc.)
    
    def get_telemetry_summary(self) -> Dict:
        """Get telemetry summary."""
        return {
            "file_id": self.file_id,
            "filename": self.filename,
            "upload_time": self.upload_time.isoformat(),
            "data_points": len(self.parsed_data.get("messages", [])),
        }


@dataclass
class TelemetryData:
    """Telemetry data entity"""
    timestamp: float
    message_type: str
    data: Dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "message_type": self.message_type,
            "data": self.data,
        }

