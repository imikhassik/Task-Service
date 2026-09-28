import time
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

#   Distinct log entry
class LogEntry(BaseModel):
    sequence: int
    timestamp: float
    event_type: str  # 'function_call', 'output', 'error'
    name: str
    duration_ms: Optional[float] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_timestamp_ms(self) -> int:
        return int(self.timestamp * 1000) if self.timestamp else 0


#   Information from JWT token
class TokenInfo(BaseModel):
    data: Any                       # sub contents (can be a string, an object, etc.)
    issued: Optional[int] = None    # timestamp from iat
    expired: Optional[int] = None   # timestamp from exp

#   Log batch for one session
class SessionLogPackage(BaseModel):
    session_id: UUID
    service_name: str
    project_id: Optional[str] = None
    token: Optional[TokenInfo] = None
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    entries: List[LogEntry] = Field(default_factory=list)
    error: Optional[str] = None

    def add_entry(self, entry: LogEntry):
        self.entries.append(entry)

    def close(self):
        self.end_time = time.time()

    def get_total_duration_ms(self) -> Optional[float]:
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time) * 1000
        return None

    def to_json(self) -> str:
        import json

        data = {
            "service_name": self.service_name,
            "session_id": str(self.session_id),
            "project_id": self.project_id if self.project_id else None,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_ms": self.get_total_duration_ms(),
            "entries": [
                {
                    "sequence": e.sequence,
                    "timestamp": e.timestamp,
                    "timestamp_ms": e.get_timestamp_ms(),
                    "event_type": e.event_type,
                    "name": e.name,
                    "duration_ms": e.duration_ms,
                    "input_data": e.input_data,
                    "output_data": e.output_data,
                    "error": e.error,
                    "metadata": e.metadata
                }
                for e in self.entries
            ]
        }

        if self.token:
            token_dict = {}
            if self.token.data is not None:
                token_dict["data"] = self.token.data
            if self.token.issued is not None:
                token_dict["issued"] = self.token.issued
            if self.token.expired is not None:
                token_dict["expired"] = self.token.expired
            if token_dict:
                data["token"] = token_dict

        if self.error:
            data["error"] = self.error

        return json.dumps(data, ensure_ascii=False, default=str)