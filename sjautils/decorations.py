import random
from functools import wraps

def synchronized(func):
    @wraps(func)
    def _guarded(*args, **kwargs):
        lock = args[0]._instance_lock
        with lock:
            return func(*args, **kwargs)
    return _guarded

def abstract(func):
    @wraps(func)
    def inner(*args, **kwargs):
      raise Exception('%s needs a non-abstract implementation' % func.__name__)
    return inner


