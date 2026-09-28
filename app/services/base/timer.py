"""
Timer use insruction: https://git.infra.cloveri.com/eitica/knowhow/wiki/-/wikis/Comp/Service
"""
    
import time
import asyncio

from functools import wraps


class Timer:
    def __init__(self):
        self._time = {}
        self._order = []

    def start(self, name):
        if name not in self._time:
            self._time[name] = {}
            self._order.append(name)
        self._time[name]['start'] = time.time()

    def finish(self, name):
        if name not in self._time or 'start' not in self._time[name]:
            raise ValueError(f"Timer for '{name}' was not started.")
        self._time[name]['finish'] = time.time()

    def dump(self):
        # Return a structured dictionary with order and timings
        return {
            "order": self._order,
            "time": self._time
        }


def timed(is_root=False):
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, timer, **kwargs):
                timer.start(func.__name__)
                try:
                    return await func(*args, timer=timer, **kwargs)
                finally:
                    timer.finish(func.__name__)
                    if is_root:
                        print(timer.dump())
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, timer, **kwargs):
                timer.start(func.__name__)
                try:
                    return func(*args, timer=timer, **kwargs)
                finally:
                    timer.finish(func.__name__)
                    if is_root:
                        print(timer.dump())
            return sync_wrapper
    return decorator


def get_timer():
    return Timer()
