import traceback
from functools import wraps

def exception_trace(exc):
    return traceback.format_exception(exc)

def get_exception_handler(logger):
    def async_handle_exception(fn):
        @wraps(fn)
        async def inner(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                logger.exception(e)
                return {'exception': exception_trace(e)}
        return inner
    return async_handle_exception



