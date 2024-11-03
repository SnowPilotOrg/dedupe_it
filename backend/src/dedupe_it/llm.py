from functools import lru_cache
import anthropic


@lru_cache(maxsize=1)
def get_anthropic_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic()
