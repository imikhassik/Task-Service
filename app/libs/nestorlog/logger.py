import asyncio
import sys
import time
from typing import Optional, Any, Dict, Union
from uuid import UUID

from .context import (
    get_current_session, set_current_session,
    get_next_sequence, reset_sequence, clear_context
)
from .models import LogEntry, SessionLogPackage, TokenInfo
from .handlers import get_handler
from .config import config

#   Checks whether the field is reserved Pydantic field
def _is_pydantic_special_field(field_name: str) -> bool:
    pydantic_special_fields = {
        'model_computed_fields',
        'model_config',
        'model_extra',
        'model_fields',
        'model_fields_set',
        'model_post_init',
        '__pydantic_initialised__',
        '__pydantic_validator__',
        '__pydantic_private__',
        '__pydantic_extra__',
        '__fields__',
        '__validators__',
        '__config__',
        '__schema__',
    }
    return field_name in pydantic_special_fields or field_name.startswith('_pydantic_')


#   Checks whether the object is Pydantic model
def _is_pydantic_model(obj: Any) -> bool:
    return hasattr(obj, '__class__') and hasattr(obj.__class__, 'model_config')


#   Masks sensitive data fields recursively
def mask_sensitive_data(data: Any, field_name: str = None, depth: int = 0) -> Any:
    if not config.mask_enabled:
        return data

    if depth > 10:
        return "<max depth reached>"

    if field_name and _is_sensitive_field(field_name):
        return mask_sensitive_value(data)

    # Transform Pydantic models into dicts
    if _is_pydantic_model(data):
        try:
            if hasattr(data, 'model_dump'):
                data = data.model_dump()
            elif hasattr(data, 'dict'):
                data = data.dict()
        except Exception: # NOQA: S110
            pass

    if isinstance(data, dict):
        masked = {}
        for key, val in data.items():
            if _is_pydantic_special_field(key):
                continue
            if _is_sensitive_field(key):
                masked[key] = mask_sensitive_value(val)
            else:
                masked[key] = mask_sensitive_data(val, key, depth + 1)
        return masked

    elif isinstance(data, list):
        return [mask_sensitive_data(item, field_name, depth + 1) for item in data]

    elif isinstance(data, tuple):
        return tuple(mask_sensitive_data(item, field_name, depth + 1) for item in data)

    elif hasattr(data, '__dict__') and not isinstance(data, (str, int, float, bool, type(None))):
        try:
            obj_dict = {}
            for attr_name in dir(data):
                if attr_name.startswith('_'):
                    continue
                if _is_pydantic_special_field(attr_name):
                    continue
                try:
                    attr_value = getattr(data, attr_name)
                    if callable(attr_value):
                        continue
                except Exception: # NOQA: S112
                    continue

                try:
                    if _is_sensitive_field(attr_name):
                        obj_dict[attr_name] = mask_sensitive_value(attr_value)
                    else:
                        obj_dict[attr_name] = mask_sensitive_data(attr_value, attr_name, depth + 1)
                except Exception:
                    obj_dict[attr_name] = "<unable to access>"
            return obj_dict
        except Exception:
            return str(data)

    elif data is None:
        return None

    else:
        return data

#   Check whether a field is sensitive
def _is_sensitive_field(field_name: str) -> bool:
    if not field_name:
        return False
    return field_name.lower() in [f.lower() for f in config.sensitive_fields]

#   Masks sensitive data
def mask_sensitive_value(value: Any) -> Any:
    if isinstance(value, str) and len(value) > 2:
        if len(value) > 6:
            return f"{value[0]}{'*' * 3}{value[-1]}"
        return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"
    elif isinstance(value, str):
        return "*" * len(value) if value else ""
    else:
        return "[MASKED]"

#   Base logger class
class Logger:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.handler = get_handler()
        self._initialized = True

    #   Truncates value if it is longer than max_bytes
    def _truncate_value(self, value: Any, max_bytes: int) -> Any:
        if max_bytes <= 0 or value is None:
            return value

        try:
            str_value = str(value)
            if len(str_value.encode('utf-8')) > max_bytes:
                return f"{str_value[:max_bytes]}...[truncated]"
        except Exception:
            return "<unable to serialize>"
        return value

    def _get_timestamp(self) -> float:
        return time.time()

    #   Starts new logging session
    #
    #   Args:
    #       session_id: Unique session identifier
    #       project_id: Project identifier (optional)
    #       token_info: Information from JWT token (optional)
    #       start_time: Sessions start time (optional)
    def start_session(
        self,
        session_id: UUID,
        project_id: Optional[str] = None,
        token_info: Optional[TokenInfo] = None,
        start_time: Optional[float] = None
    ) -> SessionLogPackage:
        existing_session = get_current_session()
        if existing_session:
            return existing_session

        session = SessionLogPackage(
            session_id=session_id,
            service_name=self.service_name,
            project_id=project_id,
            token=token_info,
            start_time=start_time or self._get_timestamp()
        )

        set_current_session(session)
        reset_sequence()
        return session

    def get_current_session(self) -> Optional[SessionLogPackage]:
        return get_current_session()

    #   Logs function call
    def log_call(self, name: str, level: str, kwargs: Dict[str, Any], start_time: float):
        if not config.is_enabled() or not config.is_level_enabled(level):
            return

        session = get_current_session()
        if not session:
            return

        sequence = get_next_sequence()

        # Masks sensitive data in input parameters
        masked_kwargs = mask_sensitive_data(kwargs)

        # Truncate values according to max size
        input_data = {}
        for key, value in masked_kwargs.items():
            input_data[key] = self._truncate_value(value, config.max_bytes)

        entry = LogEntry(
            sequence=sequence,
            timestamp=start_time,
            event_type="function_call",
            name=name,
            duration_ms=None,
            input_data=input_data if input_data else None,
            metadata={"level": level.upper()}
        )
        session.add_entry(entry)

        return sequence

    #   Update last call duration
    def update_call_duration(self, name: str, duration_ms: float):
        session = get_current_session()
        if not session or not session.entries:
            return

        # Look for the last entry with this name and function_call type
        for entry in reversed(session.entries):
            if entry.event_type == "function_call" and entry.name == name:
                entry.duration_ms = duration_ms
                break

    #   Log output data
    def log_output(self, output_data: Any, level: str = "INFO", name: Optional[str] = None):
        if not config.is_enabled() or not config.is_level_enabled(level):
            return

        session = get_current_session()
        if not session:
            return

        # Mask sensitive data in input
        masked_output = mask_sensitive_data(output_data)
        truncated_output = self._truncate_value(masked_output, config.max_bytes)

        entry = LogEntry(
            sequence=get_next_sequence(),
            timestamp=self._get_timestamp(),
            event_type="output",
            name=name or "return_value",
            output_data=truncated_output,
            metadata={"level": level.upper()}
        )
        session.add_entry(entry)

    #   Log error
    def log_error(self, error_message: str, level: str = "ERROR", name: Optional[str] = None):
        if not config.is_enabled() or not config.is_level_enabled(level):
            return

        session = get_current_session()
        if not session:
            return

        # Errors are not masked
        truncated_error = self._truncate_value(error_message, config.max_bytes)

        entry = LogEntry(
            sequence=get_next_sequence(),
            timestamp=self._get_timestamp(),
            event_type="error",
            name=name or "error",
            error=truncated_error,
            metadata={"level": level.upper()}
        )
        session.add_entry(entry)

    #   Send current log batch
    async def send_package(self):
        if not config.is_enabled():
            clear_context()
            return

        session = get_current_session()
        if not session or not session.entries:
            clear_context()
            return

        session.close()

        if config.async_send:
            asyncio.create_task(self._send_package_async(session))
        else:
            await self.handler.send(session)

        clear_context()

    async def _send_package_async(self, session: SessionLogPackage):
        try:
            await self.handler.send(session)
        except Exception as e:
            print(f"[NestorLog] Error sending log package: {e}", file=sys.stderr)

#   Update nestorlog configuration from service config object
def _update_config_from_settings(settings_obj) -> None:
    if hasattr(settings_obj, 'NLOG_ENABLED'):
        config.enabled = settings_obj.NLOG_ENABLED
    if hasattr(settings_obj, 'NLOG_LEVELS'):
        config.levels_str = settings_obj.NLOG_LEVELS
    if hasattr(settings_obj, 'NLOG_HANDLER'):
        config.handler = settings_obj.NLOG_HANDLER
    if hasattr(settings_obj, 'NLOG_MAX_BYTES'):
        config.max_bytes = settings_obj.NLOG_MAX_BYTES
    if hasattr(settings_obj, 'NLOG_TIME_PRECISION'):
        config.time_precision = settings_obj.NLOG_TIME_PRECISION
    if hasattr(settings_obj, 'NLOG_ASYNC_SEND'):
        config.async_send = settings_obj.NLOG_ASYNC_SEND
    if hasattr(settings_obj, 'NLOG_FILE_PATH'):
        config.file_path = settings_obj.NLOG_FILE_PATH
    if hasattr(settings_obj, 'NLOG_SENSITIVE_FIELDS'):
        config.sensitive_fields = settings_obj.NLOG_SENSITIVE_FIELDS
    if hasattr(settings_obj, 'NLOG_MASK_ENABLED'):
        config.mask_enabled = settings_obj.NLOG_MASK_ENABLED


_logger: Optional[Logger] = None

#   Initialize global logger
def init_logger(
    service_name: str,
    settings: Optional[Any] = None,
    **kwargs
) -> Logger:
    global _logger
    
    if settings is not None:
        _update_config_from_settings(settings)
    
    if 'enabled' in kwargs:
        config.enabled = kwargs['enabled']
    if 'levels' in kwargs:
        config.levels_str = kwargs['levels']
    if 'handler' in kwargs:
        config.handler = kwargs['handler']
    if 'file_path' in kwargs:
        config.file_path = kwargs['file_path']
    if 'max_bytes' in kwargs:
        config.max_bytes = kwargs['max_bytes']
    if 'time_precision' in kwargs:
        config.time_precision = kwargs['time_precision']
    if 'async_send' in kwargs:
        config.async_send = kwargs['async_send']
    if 'sensitive_fields' in kwargs:
        config.sensitive_fields = kwargs['sensitive_fields']
    if 'mask_enabled' in kwargs:
        config.mask_enabled = kwargs['mask_enabled']
    
    try:
        _logger = Logger(service_name)
        print(f"[NestorLog] Logger initialized: service={service_name}, handler={config.handler}, mask_enabled={config.mask_enabled}", file=sys.stderr)
        return _logger
    except Exception as e:
        print(f"[NestorLog] Failed to initialize logger: {e}", file=sys.stderr)
        raise


def get_logger() -> Optional[Logger]:
    return _logger