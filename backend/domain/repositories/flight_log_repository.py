"""飞行日志仓储接口"""
from abc import ABC, abstractmethod
from typing import Optional
from backend.domain.entities.flight_log import FlightLog


class IFlightLogRepository(ABC):
    """飞行日志仓储接口"""
    
    @abstractmethod
    async def save(self, flight_log: FlightLog) -> FlightLog:
        """保存飞行日志"""
        pass
    
    @abstractmethod
    async def get_by_id(self, file_id: str) -> Optional[FlightLog]:
        """根据ID获取飞行日志"""
        pass
    
    @abstractmethod
    async def get_telemetry_data(self, file_id: str, message_type: Optional[str] = None) -> list:
        """获取遥测数据"""
        pass
    
    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """删除飞行日志"""
        pass

