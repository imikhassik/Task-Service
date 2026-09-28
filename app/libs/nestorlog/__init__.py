"""
NestorLog - FastAPI services logging library
"""

from .decorators import nlog, nestor
from .logger import init_logger, get_logger
from .config import config
from .context import get_current_session

__all__ = [
    'nlog',
    'nestor',
    'init_logger',
    'get_logger',
    'config',
    'get_current_session'
]

__version__ = '1.2.0'