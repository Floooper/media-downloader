from functools import wraps
import logging
from typing import Optional, Any, Callable

logger = logging.getLogger(__name__)

def handle_errors(error_message: str, return_value: Any = None) -> Callable:
    """Decorator to handle errors in service methods"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"{error_message}: {str(e)}")
                return return_value
        return wrapper
    return decorator
