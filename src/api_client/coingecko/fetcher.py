"""
src/api_client/fetcher
fetch all necessary coingecko market
"""

import logging

import requests
from requests.exceptions import HTTPError

from src.api_client.coingecko.http import get_api_key, retry_action
from src.core.config import TrackerConfig


def _get(
    endpoint: str, params: dict | None, config: TrackerConfig, log: logging.Logger
) -> dict | list[dict] | None:
    """Returns the parsed JSON dict on success, or None
    if the endpoint failed after all retries.
    We deliberately should not raise here: one bad coin_id
    should never crash a 10-coin batch job.
    """
    params = dict(params or {})
    api_key = get_api_key(log)

    if api_key:
        params["x_cg_demo_api_key"] = api_key

    url = f"{config.coingecko.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def __get() -> dict | None:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            raise HTTPError(f"Rate Limited (429) on {endpoint}", response=response)
        elif response.status_code == 404:
            log.error("Not found (404): %s - check the coin_id is correct", endpoint)
            return None
        elif response.status_code == 500:
            log.error("API Connection Error (500)!")
            return None
        else:
            response.raise_for_status()

    result = retry_action(
        __get,
        log=log,
        retries=config.coingecko.max_retries,
        backoff_base=config.coingecko.backoff_base_seconds,
    )
    return result


def get_markets(
    coin_ids: list[str],
    vs_currency: str = "usd",
    *,
    config: TrackerConfig,
    log: logging.Logger,
) -> list[dict] | None:
    """
    Fetch flat markets data (price, market cap, 24h/7d change) for multiple coins in one call
    """
    params = {
        "vs_currency": vs_currency,
        "ids": ",".join(coin_ids),
        "order": "market_cap_desc",
        "price_change_percentage": "24h, 7d",
        "sparkline": "false",
    }
    log.info("Fetching market data for %d coins", len(coin_ids))
    return _get("/coins/markets", params, config, log)


def get_coin_detail(
    coin_id: str, config: TrackerConfig, log: logging.Logger
) -> dict | None:
    """Fetch deeply nested detail data for one coin - community stats, developer stats,
    and per-currency nested pricing."""
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "true",
        "developer_data": "true",
        "sparkline": "false",
    }
    log.info("- fetching detail data for '%s'", coin_id)
    return _get(coin_id, params, config, log)


def get_coin_details_batch(
    coin_ids: list[str], config: TrackerConfig, log: logging.Logger
) -> dict[str, dict | None]:
    """Fetch one coin detail for Multiple coins, one request per coin
    (this endpoint doesnt support batching - a real API limitation).
    Returns a dict keyed by coin_id."""
    results: dict[str, dict | None] = {}
    log.info("Fetching %d coin details in batch: '%s'", len(coin_ids), coin_ids)
    for coin_id in coin_ids:
        results[coin_id] = get_coin_detail(coin_id, config, log)
    return results
