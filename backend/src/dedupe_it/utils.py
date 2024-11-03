import time
import functools
import asyncio
from typing import Callable, TypeVar, ParamSpec

import anthropic
from .logger import logger

# For type hints
T = TypeVar("T")
P = ParamSpec("P")


def timing_decorator(func: Callable) -> Callable:
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} took {end - start:.2f} seconds")
        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} took {end - start:.2f} seconds")
        return result

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def with_anthropic_retry(max_retries: int = 5, initial_delay: float = 1.0):
    """
    Decorator for handling Anthropic API rate limits with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except anthropic.RateLimitError as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for rate limit"
                        )
                        raise

                    # Get retry-after from headers if available, otherwise use exponential backoff
                    retry_after = getattr(e, "retry_after", None)
                    wait_time = float(retry_after) if retry_after else delay

                    logger.warning(
                        f"Rate limit hit, attempt {attempt + 1}/{max_retries}. "
                        f"Waiting {wait_time:.2f}s before retry"
                    )

                    await asyncio.sleep(wait_time)
                    delay *= 2  # Exponential backoff

                except Exception as e:
                    # Don't retry other types of exceptions
                    raise

            raise last_exception

        return wrapper

    return decorator


class Timer:
    def __init__(self, name: str):
        self.name = name

    async def __aenter__(self):
        self.start = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        end = time.time()
        logger.info(f"{self.name} took {end - self.start:.2f} seconds")
