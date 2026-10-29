import logging
import time
from collections.abc import Callable
from typing import TypeVar

from src.core.config import Coingecko as cg_api
from src.core.exceptions import CoinGeckoError, RateLimitError, APIConnectionError


def get_api_key(log: logging.Logger) -> str | None:
    if not cg_api.api_key:
        log.warning(
            "No COINGECKO_API_KEY found in .env - falling back to the public"
            "keyless tier (30 calls/min). Get a free key at "
            "https://www.coingecko.com/en/api/pricing for higher limits"
        )
        return
    return cg_api.api_key


# ── Rate Limiting ─────────────────────────────────────────
_last_call_time: float = 0.0


def _throttle() -> None:
    """Proactively space out requests so we rarely hit a 429 in the first place.
    This is cheaper and more polite than 'call fast', then appologize."""
    global _last_call_time
    min_seconds_between_calls = (
        cg_api.min_second_api_key if cg_api.api_key else cg_api.min_second_public
    )

    elapsed = time.time() - _last_call_time
    wait = min_seconds_between_calls - elapsed

    if wait > 0:
        time.sleep(wait)
    _last_call_time = time.time()


# ── Retry Logic ─────────────────────────────────────────
T = TypeVar("T")


def retry_action(
    action: Callable[[], T],
    *,
    description: str,
    log: logging.Logger,
    retries: int = 3,
    backoff_base: float = 2,
) -> T:
    last_exception: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return action()
        except CoinGeckoError as e:
            last_exception = e
            log.warning(
                "Attempt %d/%d failed for '%s': %s", attempt, retries, description, e
            )
            if attempt < retries:
                wait_for = backoff_base * (2 ** (attempt - 1))
                log.info("Retrying '%s' in %.1fs...", description, wait_for)
                time.sleep(wait_for)

    log.error("'%s' failed after %d attempts — giving up", description, retries)
    raise last_exception  # type: ignore
