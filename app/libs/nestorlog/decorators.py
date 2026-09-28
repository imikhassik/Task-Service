import time
import sys
import inspect
import jwt
from functools import wraps
from typing import Optional, List, Callable, Any, Dict
from uuid import UUID

from .logger import get_logger
from .context import get_current_session
from .config import config
from .models import TokenInfo


"""
    Explicit data logging class
    
    Use:
        nestor.print(data, name="my_data")
        nestor.debug(data, name="debug_data")
        nestor.info(data, name="info_data")
        nestor.error(data, name="error_data")
"""
class NLogPrinter:

    @staticmethod
    def print(data: Any, level: str = "INFO", name: Optional[str] = None):
        logger = get_logger()
        if not logger:
            return

        session = get_current_session()
        if not session:
            return

        logger.log_output(data, level=level, name=name)

    @staticmethod
    def debug(data: Any, name: Optional[str] = None):
        logger = get_logger()
        if not logger:
            return

        session = get_current_session()
        if not session:
            return

        logger.log_output(data, level="DEBUG", name=name)

    @staticmethod
    def info(data: Any, name: Optional[str] = None):
        logger = get_logger()
        if not logger:
            return

        session = get_current_session()
        if not session:
            return

        logger.log_output(data, level="INFO", name=name)

    @staticmethod
    def error(data: Any, name: Optional[str] = None):
        logger = get_logger()
        if not logger:
            return

        session = get_current_session()
        if not session:
            return

        logger.log_output(data, level="ERROR", name=name)


nestor = NLogPrinter()

#   Extracts request from args or kwargs
def _extract_request_from_args(args, kwargs):
    request = kwargs.get('request')
    if request is not None:
        return request

    if args:
        first_arg = args[0]
        if hasattr(first_arg, 'state') and hasattr(first_arg, 'headers'):
            return first_arg

    return None

"""
    Extracts information from JWT token in Authorization header.

    Returns TokenInfo with:
    - data: sub contents (can be a string, an object, etc.)
    - issued: timestamp from iat
    - expired: timestamp from exp
"""
def _extract_token_info_from_request(request) -> Optional[TokenInfo]:
    if not request:
        return None

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    token = parts[1]

    try:
        # Decorating without signature validation (we only need sub, iat, exp fields)
        decoded = jwt.decode(token, options={"verify_signature": False})

        sub = decoded.get('sub')
        iat = decoded.get('iat')
        exp = decoded.get('exp')

        return TokenInfo(
            data=sub,
            issued=iat,
            expired=exp
        )
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

#   Extracts project_id from function parameters.
#   Supports 'project_id' parameter name or Header annotation with alias
def _extract_project_id_from_args(func, args, kwargs, exclude):
    try:
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Looking for project_id in parameters
        for param_name, param_value in bound_args.arguments.items():
            if param_name == 'project_id':
                return str(param_value) if param_value else None
            # Checking annotation for Header
            param = sig.parameters.get(param_name)
            if param and hasattr(param, 'annotation'):
                annotation = param.annotation
                # Checking if Header parameter has PROJECT_ID alias
                if hasattr(annotation, '__metadata__'):
                    for meta in annotation.__metadata__:
                        if hasattr(meta, 'alias') and meta.alias == 'X-Project-ID':
                            return str(param_value) if param_value else None
    except Exception: # NOQA: S110
        pass

    return None

#   Extracts exception code
def _extract_error_code(exception: Exception) -> Optional[str]:
    if hasattr(exception, 'code') and exception.code:
        return str(exception.code)

    if hasattr(exception, 'detail'):
        detail = exception.detail
        if hasattr(detail, 'code') and detail.code:
            return str(detail.code)
        if isinstance(detail, dict) and detail.get('code'):
            return str(detail.get('code'))

    if hasattr(exception, 'status_code') and exception.status_code:
        return f"HTTP_{exception.status_code}"

    if exception.__class__.__name__ in ['ForbiddenException', 'UserUnauthorizedException']:
        return exception.__class__.__name__.upper()

    return exception.__class__.__name__

#   Creates decorator with specified parameters
def _create_decorator(
    level: str = "INFO",
    log_input: bool = True,
    log_output: bool = True,
    name: Optional[str] = None,
    exclude: Optional[List[str]] = None
):
    if exclude is None:
        exclude = []

    # Automatically add 'request' to exception list
    if 'request' not in exclude:
        exclude = exclude + ['request']

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger()
            if not logger:
                print("[NestorLog] Logger not initialized", file=sys.stderr)
                return await func(*args, **kwargs)

            session = get_current_session()

            if not session:
                request = _extract_request_from_args(args, kwargs)
                session_id_str = None

                if request and hasattr(request.state, 'session_id'):
                    session_id_str = request.state.session_id
                else:
                    try:
                        from app.libs.session_context import get_session_id_str
                        session_id_str = get_session_id_str()
                    except ImportError:
                        pass

                if session_id_str:
                    try:
                        session_id = UUID(session_id_str)

                        # Extract project_id from function parameters
                        project_id = _extract_project_id_from_args(func, args, kwargs, exclude)

                        # Extract information from JWT token
                        token_info = _extract_token_info_from_request(request)

                        session = logger.start_session(
                            session_id=session_id,
                            project_id=project_id,
                            token_info=token_info
                        )
                    except ValueError:
                        print(f"[NestorLog] Invalid session_id format: {session_id_str}", file=sys.stderr)
                        return await func(*args, **kwargs)
                else:
                    print("[NestorLog] No session_id found. Did you add SessionContextMiddleware?", file=sys.stderr)
                    return await func(*args, **kwargs)

            start_time = time.time()
            call_name = name or func.__name__

            # Log input data BEFORE function call
            if log_input and config.is_level_enabled(level):
                kwargs_to_log: Dict[str, Any] = {}

                # Process keyword arguments
                for key, value in kwargs.items():
                    if key not in exclude:
                        kwargs_to_log[key] = value

                # Process positional arguments
                if args:
                    sig = inspect.signature(func)
                    param_names = list(sig.parameters.keys())

                    for i, arg in enumerate(args):
                        if i < len(param_names) and param_names[i] not in exclude:
                            kwargs_to_log[param_names[i]] = arg

                logger.log_call(
                    name=call_name,
                    level=level,
                    kwargs=kwargs_to_log,
                    start_time=start_time
                )

            try:
                result = await func(*args, **kwargs)

                # Update call duration
                duration_ms = (time.time() - start_time) * 1000
                logger.update_call_duration(call_name, duration_ms)

                # Log input data after successful call
                if log_output and config.is_level_enabled(level):
                    if hasattr(result, 'code') and result.code:
                        logger.log_output(
                            output_data={"code": result.code},
                            level=level,
                            name="response_code"
                        )

                    logger.log_output(
                        output_data=result,
                        level=level,
                        name="return_value"
                    )

                return result

            except Exception as e:
                # Updte call duration before exception
                duration_ms = (time.time() - start_time) * 1000
                logger.update_call_duration(call_name, duration_ms)

                error_code = _extract_error_code(e)
                error_message = str(e) if str(e) else e.__class__.__name__

                logger.log_error(
                    error_message=error_message,
                    level="ERROR",
                    name=func.__name__
                )

                logger.log_output(
                    output_data={"code": error_code},
                    level="ERROR",
                    name="error_code"
                )

                raise

            finally:
                await logger.send_package()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger()
            if not logger:
                print("[NestorLog] Logger not initialized", file=sys.stderr)
                return func(*args, **kwargs)

            session = get_current_session()

            if not session:
                request = _extract_request_from_args(args, kwargs)
                session_id_str = None

                if request and hasattr(request.state, 'session_id'):
                    session_id_str = request.state.session_id
                else:
                    try:
                        from app.libs.session_context import get_session_id_str
                        session_id_str = get_session_id_str()
                    except ImportError:
                        pass

                if session_id_str:
                    try:
                        session_id = UUID(session_id_str)
                        
                        project_id = _extract_project_id_from_args(func, args, kwargs, exclude)
                        token_info = _extract_token_info_from_request(request)
                        
                        session = logger.start_session(
                            session_id=session_id,
                            project_id=project_id,
                            token_info=token_info
                        )
                    except ValueError:
                        print(f"[NestorLog] Invalid session_id format: {session_id_str}", file=sys.stderr)
                        return func(*args, **kwargs)
                else:
                    print("[NestorLog] No session_id found", file=sys.stderr)
                    return func(*args, **kwargs)

            start_time = time.time()
            call_name = name or func.__name__

            if log_input and config.is_level_enabled(level):
                kwargs_to_log: Dict[str, Any] = {}

                for key, value in kwargs.items():
                    if key not in exclude:
                        kwargs_to_log[key] = value

                if args:
                    sig = inspect.signature(func)
                    param_names = list(sig.parameters.keys())

                    for i, arg in enumerate(args):
                        if i < len(param_names) and param_names[i] not in exclude:
                            kwargs_to_log[param_names[i]] = arg

                logger.log_call(
                    name=call_name,
                    level=level,
                    kwargs=kwargs_to_log,
                    start_time=start_time
                )

            try:
                result = func(*args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000
                logger.update_call_duration(call_name, duration_ms)

                if log_output and config.is_level_enabled(level):
                    if hasattr(result, 'code') and result.code:
                        logger.log_output(
                            output_data={"code": result.code},
                            level=level,
                            name="response_code"
                        )

                    logger.log_output(
                        output_data=result,
                        level=level,
                        name="return_value"
                    )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.update_call_duration(call_name, duration_ms)

                error_code = _extract_error_code(e)
                error_message = str(e) if str(e) else e.__class__.__name__

                logger.log_error(
                    error_message=error_message,
                    level="ERROR",
                    name=func.__name__
                )

                logger.log_output(
                    output_data={"code": error_code},
                    level="ERROR",
                    name="error_code"
                )

                raise

            finally:
                import asyncio
                try:
                    loop = asyncio.get_running_loop() # NOQA: F841
                    asyncio.create_task(logger.send_package())
                except RuntimeError:
                    asyncio.run(logger.send_package())

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


#   Function calls logging decorator
#
#    Supports two modes of use:
#    1. @nlog  (no parameters)
#    2. @nlog(level="DEBUG", exclude=["request"])  (with parameters)
#
#    Specifics:
#    - request is excluded from logs (no need to specify exclude=["request"])
#    - token information is extracted from JWT token automatically (sub, iat, exp)
#    - project_id is extracted from function parameters automatically
#
#    Args:
#        level: Loggin level (DEBUG, INFO, ERROR). Default: "INFO"
#        log_input: Log input data. Default: True 
#        log_output: Log output data. Default: True
#        name: Function name in log (function name is used in case of None)
#        exclude: Parameter name list which don't need to be logged

def nlog(
    level: str = "INFO",
    log_input: bool = True,
    log_output: bool = True,
    name: Optional[str] = None,
    exclude: Optional[List[str]] = None
):
    # Check whether the call didn't have any parameters: @nlog
    if callable(level):
        func = level
        return _create_decorator()(func)

    # Call with parameters: @nlog(...)
    return _create_decorator(
        level=level,
        log_input=log_input,
        log_output=log_output,
        name=name,
        exclude=exclude
    )