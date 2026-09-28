import contextvars
from uuid import UUID, uuid4
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

__version__ = '1.0.0'

_current_session_id: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar(
    'current_session_id', default=None
)


def get_session_id() -> Optional[UUID]:
    return _current_session_id.get()


def get_session_id_str() -> Optional[str]:
    session_id = get_session_id()
    return str(session_id) if session_id else None


def set_session_id(session_id: UUID):
    _current_session_id.set(session_id)


def clear_session_id():
    _current_session_id.set(None)


class SessionContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        session_id_str = request.headers.get('X-Session-ID')
        
        if session_id_str:
            try:
                session_id = UUID(session_id_str)
            except ValueError:
                session_id = uuid4()
        else:
            session_id = uuid4()
        
        set_session_id(session_id)
        request.state.session_id = str(session_id)
        
        try:
            response = await call_next(request)
            return response
        finally:
            clear_session_id()