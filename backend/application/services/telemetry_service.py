"""Telemetry data service"""
from typing import Dict, List, Optional
from backend.domain.repositories.flight_log_repository import IFlightLogRepository
from backend.domain.entities.flight_log import FlightLog


class TelemetryService:
    """Telemetry service - provides query and analysis capabilities"""
    
    def __init__(self, flight_log_repository: IFlightLogRepository):
        self.flight_log_repository = flight_log_repository
        self._summary_cache: Dict[str, Dict] = {}
    
    def invalidate_cache(self, file_id: Optional[str] = None):
        """Invalidate cached summaries."""
        if file_id:
            self._summary_cache.pop(file_id, None)
        else:
            self._summary_cache.clear()
    
    async def get_flight_summary(self, file_id: str) -> Dict:
        """Get flight summary information (cached)."""
        if file_id in self._summary_cache:
            return self._summary_cache[file_id]
        
        flight_log = await self.flight_log_repository.get_by_id(file_id)
        if not flight_log:
            return {}
        
        telemetry = await self.flight_log_repository.get_telemetry_data(file_id)
        
        # Extract key metrics
        summary = {
            "file_id": file_id,
            "filename": flight_log.filename,
            "total_messages": len(telemetry),
            "message_types": self._extract_message_types(telemetry),
        }
        
        # Extract time range
        if telemetry:
            timestamps = [msg.get("timestamp", 0) for msg in telemetry if "timestamp" in msg]
            if timestamps:
                summary["time_range"] = {
                    "start": min(timestamps),
                    "end": max(timestamps),
                    "duration": max(timestamps) - min(timestamps),
                }
        
        self._summary_cache[file_id] = summary
        return summary
    
    async def query_telemetry(
        self, 
        file_id: str, 
        message_type: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Query telemetry data."""
        data = await self.flight_log_repository.get_telemetry_data(file_id, message_type)
        
        if filters:
            data = self._apply_filters(data, filters)
        
        return data
    
    def _extract_message_types(self, telemetry: List[Dict]) -> List[str]:
        """Extract message types."""
        types = set()
        for msg in telemetry:
            if "message_type" in msg:
                types.add(msg["message_type"])
        return sorted(list(types))
    
    def _apply_filters(self, data: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filter conditions."""
        filtered = data
        
        if "min_timestamp" in filters:
            filtered = [msg for msg in filtered if msg.get("timestamp", 0) >= filters["min_timestamp"]]
        
        if "max_timestamp" in filters:
            filtered = [msg for msg in filtered if msg.get("timestamp", 0) <= filters["max_timestamp"]]
        
        return filtered

