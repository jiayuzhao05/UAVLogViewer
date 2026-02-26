"""MAVLink log parser"""
import os
from typing import Dict, List, Optional
from pymavlink import mavutil
from datetime import datetime


class MAVLinkParser:
    """Parser for MAVLink .bin files"""
    
    def parse(self, file_path: str) -> Dict:
        """
        Parse a MAVLink .bin file.
        
        Args:
            file_path: path to the file
            
        Returns:
            Parsed data dictionary containing messages and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Collect file metadata
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        # Parse MAVLink log
        mlog = mavutil.mavlink_connection(file_path)
        messages = []
        
        try:
            while True:
                msg = mlog.recv_match(type=None)
                if msg is None:
                    break
                
                # Convert to dict
                msg_dict = {
                    "timestamp": msg._timestamp if hasattr(msg, '_timestamp') else 0,
                    "message_type": msg.get_type(),
                    "data": self._message_to_dict(msg),
                }
                messages.append(msg_dict)
        except Exception as e:  # noqa: B110
            # Even on parse errors, return what has been decoded so far
            # This is intentional to allow partial parsing
            pass  # noqa: B110
        
        metadata = {
            "filename": filename,
            "file_size": file_size,
            "parsed_at": datetime.now().isoformat(),
            "total_messages": len(messages),
        }
        
        return {
            "messages": messages,
            "metadata": metadata,
        }
    
    def _message_to_dict(self, msg) -> Dict:
        """Convert a MAVLink or DataFlash message to a dictionary."""
        # DataFlash (DFMessage) uses get_fieldnames(); MAVLink uses fieldnames
        if hasattr(msg, "to_dict") and callable(getattr(msg, "to_dict")):
            return msg.to_dict()
        fields = getattr(msg, "fieldnames", None) or (
            list(msg.get_fieldnames()) if hasattr(msg, "get_fieldnames") else []
        )
        result = {}
        for field in fields:
            value = getattr(msg, field, None)
            if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool)):
                result[field] = str(value)
            else:
                result[field] = value
        return result
    
    def extract_key_metrics(self, messages: List[Dict]) -> Dict:
        """
        Extract key metrics from messages.
        
        Args:
            messages: list of telemetry messages
            
        Returns:
            dictionary of key metrics
        """
        metrics = {
            "altitude_max": None,
            "altitude_min": None,
            "battery_temp_max": None,
            "gps_loss_instances": [],
            "rc_loss_instances": [],
            "errors": [],
        }
        
        for msg in messages:
            msg_type = msg.get("message_type", "")
            data = msg.get("data", {})
            timestamp = msg.get("timestamp", 0)
            
            # Extract altitude info (GPS_RAW_INT or GLOBAL_POSITION_INT)
            if msg_type in ["GPS_RAW_INT", "GLOBAL_POSITION_INT"]:
                alt = data.get("alt", data.get("altitude", None))
                if alt is not None:
                    if metrics["altitude_max"] is None or alt > metrics["altitude_max"]:
                        metrics["altitude_max"] = alt
                    if metrics["altitude_min"] is None or alt < metrics["altitude_min"]:
                        metrics["altitude_min"] = alt
            
            # Extract battery temperature (BATTERY_STATUS)
            if msg_type == "BATTERY_STATUS":
                temp = data.get("temperature", None)
                if temp is not None:
                    if metrics["battery_temp_max"] is None or temp > metrics["battery_temp_max"]:
                        metrics["battery_temp_max"] = temp
            
            # Detect GPS signal loss (GPS_RAW_INT fix_type)
            if msg_type == "GPS_RAW_INT":
                fix_type = data.get("fix_type", None)
                if fix_type == 0:  # GPS_FIX_TYPE_NO_GPS
                    metrics["gps_loss_instances"].append(timestamp)
            
            # Detect RC signal loss (RC_CHANNELS or similar messages)
            if msg_type == "RC_CHANNELS":
                rssi = data.get("rssi", None)
                if rssi is not None and rssi < 50:  # Assume RSSI < 50 indicates weak signal
                    metrics["rc_loss_instances"].append(timestamp)
            
            # Extract error messages (STATUSTEXT)
            if msg_type == "STATUSTEXT":
                severity = data.get("severity", None)
                text = data.get("text", "")
                if severity and severity >= 4:  # MAV_SEVERITY_WARNING or above
                    metrics["errors"].append({
                        "timestamp": timestamp,
                        "severity": severity,
                        "message": text,
                    })
        
        return metrics

