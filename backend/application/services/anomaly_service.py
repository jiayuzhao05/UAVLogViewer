"""Anomaly analysis service for flight telemetry."""
from typing import Dict, List, Optional


class AnomalyService:
    """Lightweight heuristic analyzer for telemetry data with simple caching."""

    def __init__(self):
        self._cache: Dict[str, Dict] = {}

    def invalidate(self, file_id: Optional[str] = None):
        """Invalidate cached anomaly summaries."""
        if file_id:
            self._cache.pop(file_id, None)
        else:
            self._cache.clear()

    def summarize_anomalies_cached(self, file_id: str, telemetry: List[Dict]) -> Dict:
        """Return cached anomaly summary if available, otherwise compute and cache."""
        if file_id in self._cache:
            return self._cache[file_id]
        summary = self.summarize_anomalies(telemetry)
        self._cache[file_id] = summary
        return summary

    def summarize_anomalies(self, telemetry: List[Dict]) -> Dict:
        """Produce an anomaly-oriented summary for downstream reasoning."""
        if not telemetry:
            return {"status": "no_data", "notes": ["No telemetry available."]}

        findings = []
        counts = {
            "gps_loss": 0,
            "rc_loss": 0,
            "high_severity_errors": 0,
            "battery_temp_high": 0,
        }

        # Track ranges
        altitude_range = {"min": None, "max": None}
        battery_temp_max = None

        for msg in telemetry:
            msg_type = msg.get("message_type")
            data = msg.get("data", {})
            ts = msg.get("timestamp", 0)

            # Altitude extremes
            if msg_type in ["GPS_RAW_INT", "GLOBAL_POSITION_INT"]:
                alt = data.get("alt", data.get("altitude"))
                if alt is not None:
                    if altitude_range["max"] is None or alt > altitude_range["max"]:
                        altitude_range["max"] = alt
                    if altitude_range["min"] is None or alt < altitude_range["min"]:
                        altitude_range["min"] = alt

            # Battery temperature
            if msg_type == "BATTERY_STATUS":
                temp = data.get("temperature")
                if temp is not None:
                    if battery_temp_max is None or temp > battery_temp_max:
                        battery_temp_max = temp
                    # heuristic high temp threshold
                    if temp >= 60:
                        counts["battery_temp_high"] += 1
                        findings.append(
                            {
                                "type": "battery_overheat",
                                "timestamp": ts,
                                "detail": f"Battery temp high ({temp}C)",
                            }
                        )

            # GPS loss
            if msg_type == "GPS_RAW_INT":
                fix_type = data.get("fix_type")
                if fix_type == 0:
                    counts["gps_loss"] += 1
                    findings.append(
                        {
                            "type": "gps_loss",
                            "timestamp": ts,
                            "detail": "GPS fix lost (fix_type=0)",
                        }
                    )

            # RC link weak
            if msg_type == "RC_CHANNELS":
                rssi = data.get("rssi")
                if rssi is not None and rssi < 50:
                    counts["rc_loss"] += 1
                    findings.append(
                        {
                            "type": "rc_signal_weak",
                            "timestamp": ts,
                            "detail": f"RC RSSI low ({rssi})",
                        }
                    )

            # Status text errors
            if msg_type == "STATUSTEXT":
                severity = data.get("severity")
                text = data.get("text", "")
                if severity is not None and severity >= 4:
                    counts["high_severity_errors"] += 1
                    findings.append(
                        {
                            "type": "status_error",
                            "timestamp": ts,
                            "detail": f"Severity {severity}: {text}",
                        }
                    )

        summary = {
            "status": "ok" if findings else "clean",
            "counts": counts,
            "altitude_range": altitude_range,
            "battery_temp_max": battery_temp_max,
            "examples": findings[:5],  # cap to keep context compact
            "notes": [],
        }

        if not findings:
            summary["notes"].append("No obvious anomalies detected by heuristics.")
        else:
            summary["notes"].append("Heuristic findings included; verify with LLM reasoning.")

        return summary

