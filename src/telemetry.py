import functools
import logging
import time
from typing import Any, Callable

LOGGER = logging.getLogger(__name__)

def profile_time(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        LOGGER.info(f"[PROFILER] {func.__name__} ejecutada en {elapsed_time:.4f} segundos.")
        return result
    return wrapper