import contextvars
from typing import Optional
from .models import SessionLogPackage


_current_session: contextvars.ContextVar[Optional[SessionLogPackage]] = contextvars.ContextVar(
    'current_session', default=None
)
_current_sequence: contextvars.ContextVar[int] = contextvars.ContextVar(
    'current_sequence', default=0
)

#   Get current log batch
def get_current_session() -> Optional[SessionLogPackage]:
    return _current_session.get()


#   Set current log batch
def set_current_session(session: SessionLogPackage):
    _current_session.set(session)


#   Get next sequential number
def get_next_sequence() -> int:
    seq = _current_sequence.get()
    _current_sequence.set(seq + 1)
    return seq


#   Reset sequence counter
def reset_sequence():
    _current_sequence.set(0)


#   Clear context
def clear_context():
    _current_session.set(None)
    _current_sequence.set(0)