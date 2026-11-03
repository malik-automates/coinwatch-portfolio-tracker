import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from src.api_client.coingecko.fetcher import get_markets
from src.core.config import TrackerConfig
from src.ingestion.loader import load_watchlist_holding


def get_coingecko_markets(
    type: str = "default", *, config: TrackerConfig, log: logging.Logger
) -> list[dict[str, Any]] | None:
    """Return CoinGecko market data from cache or fetch it when the cache is absent.

    ``type`` may be ``default`` for full market records, ``coins`` for coin IDs,
    or ``price`` for current prices.
    """
    if type not in {"default", "coins", "price"}:
        raise ValueError(f"Unsupported market cache type: {type}")

    cache_dir = config.cache_dir
    latest_price_file = max(
        cache_dir.glob("price_*.json"),
        key=lambda file: file.stat().st_mtime,
        default=None,
    )
    if type == "price":
        filepath = latest_price_file
    else:
        filename = "markets.json" if type == "default" else "coins.json"
        filepath = cache_dir / filename

    def read_json(path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list) or any(
            not isinstance(item, dict) for item in data
        ):
            raise ValueError(f"Expected a JSON list of objects in cache file: {path}")
        return data

    def write_json(data: list[dict[str, Any]]) -> Path:
        if type == "price":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            path = cache_dir / f"price_{timestamp}.json"
        else:
            filename = "markets.json" if type == "default" else "coins.json"
            path = cache_dir / filename
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=4)
        log.info("Market '%s' fetch successfully and save to : '%s'", type, path)
        return path

    if filepath is not None and filepath.exists():
        return read_json(filepath)

    log.info("No cache found for market type '%s' - fetching markets externally", type)
    holdings = load_watchlist_holding(config.raw_watchlist_filepath, log)
    coin_ids = sorted(set(holdings[config.columns.coin_id]))
    results = get_markets(coin_ids, config=config, log=log)
    if results is None:
        log.info("Error failed to fetch markets from CoinGecko")
        return None

    if type == "coins":
        data = [{"id": item["id"], "symbol": item["symbol"]} for item in results]
    elif type == "price":
        data = [
            {
                "coin_id": item["id"],
                "ticker": item["symbol"],
                "current_price": item["current_price"],
            }
            for item in results
        ]
    else:
        data = [
            {
                "coin_id": item["id"],
                "ticker": item["symbol"],
                "current_price": item["current_price"],
                "high_24h": item["high_24h"],
                "low_24h": item["low_24h"],
                "price_change_24": item["price_change_24h"],
            }
            for item in results
        ]

    cache_filepath = write_json(data)
    return read_json(cache_filepath)
