import json
import logging
import os

import pandas as pd
import pytest

from src.api_client import utils
from src.core.config import TrackerConfig


@pytest.fixture
def config(tmp_path):
    return TrackerConfig(
        data_dir=tmp_path / "data",
        final_dir=tmp_path / "final",
        processed_dir=tmp_path / "processed",
        cache_dir=tmp_path / "cache",
        raw_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        report_dir=tmp_path / "reports",
        watchlist_filename=tmp_path / "watchlist.csv",
    )


@pytest.fixture
def logger():
    return logging.getLogger("test.api_client.utils")


@pytest.fixture
def holdings(monkeypatch):
    frame = pd.DataFrame({"coin_id": ["ethereum", "bitcoin", "bitcoin"]})
    monkeypatch.setattr(utils, "load_watchlist_holding", lambda filename, log: frame)
    return frame


def _market_records():
    return [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "current_price": 65000,
            "high_24h": 66000,
            "low_24h": 64000,
            "price_change_24h": 1.5,
        },
        {
            "id": "ethereum",
            "symbol": "eth",
            "current_price": 3000,
            "high_24h": 3100,
            "low_24h": 2900,
            "price_change_24h": -0.5,
        },
    ]


def test_default_cache_miss_fetches_transforms_and_caches(
    monkeypatch, config, logger, holdings
):
    requested_ids = []
    records = _market_records()

    def fake_get_markets(coin_ids, *, config, log):
        requested_ids.extend(coin_ids)
        return records

    monkeypatch.setattr(utils, "get_markets", fake_get_markets)

    result = utils.get_coingecko_markets(config=config, log=logger)

    assert requested_ids == ["bitcoin", "ethereum"]
    assert result == [
        {
            "coin_id": "bitcoin",
            "ticker": "btc",
            "current_price": 65000,
            "high_24h": 66000,
            "low_24h": 64000,
            "price_change_24": 1.5,
        },
        {
            "coin_id": "ethereum",
            "ticker": "eth",
            "current_price": 3000,
            "high_24h": 3100,
            "low_24h": 2900,
            "price_change_24": -0.5,
        },
    ]
    assert json.loads((config.cache_dir / "markets.json").read_text()) == result


def test_cache_hit_returns_cached_records_without_loading_or_fetching(
    monkeypatch, config, logger
):
    cached = [{"coin_id": "bitcoin", "ticker": "btc", "current_price": 65000}]
    (config.cache_dir / "markets.json").write_text(json.dumps(cached))

    def unexpected_call(*args, **kwargs):
        pytest.fail("A valid cache hit should not load holdings or call the API")

    monkeypatch.setattr(utils, "load_watchlist_holding", unexpected_call)
    monkeypatch.setattr(utils, "get_markets", unexpected_call)

    assert utils.get_coingecko_markets(config=config, log=logger) == cached


def test_coins_type_returns_validator_compatible_ids_and_caches(
    monkeypatch, config, logger, holdings
):
    monkeypatch.setattr(utils, "get_markets", lambda *args, **kwargs: _market_records())

    expected = [
        {"id": "bitcoin", "symbol": "btc"},
        {"id": "ethereum", "symbol": "eth"},
    ]
    assert utils.get_coingecko_markets(type="coins", config=config, log=logger) == expected
    assert json.loads((config.cache_dir / "coins.json").read_text()) == expected

    monkeypatch.setattr(
        utils,
        "get_markets",
        lambda *args, **kwargs: pytest.fail("Coin list should be served from cache"),
    )
    assert utils.get_coingecko_markets(type="coins", config=config, log=logger) == expected


def test_price_type_writes_timestamped_cache_and_returns_price_fields(
    monkeypatch, config, logger, holdings
):
    monkeypatch.setattr(utils, "get_markets", lambda *args, **kwargs: _market_records())

    result = utils.get_coingecko_markets(type="price", config=config, log=logger)

    assert result == [
        {"coin_id": "bitcoin", "ticker": "btc", "current_price": 65000},
        {"coin_id": "ethereum", "ticker": "eth", "current_price": 3000},
    ]
    assert len(list(config.cache_dir.glob("price_*.json"))) == 1
    assert json.loads(next(config.cache_dir.glob("price_*.json")).read_text()) == result


def test_price_type_uses_most_recent_price_cache(monkeypatch, config, logger):
    older = config.cache_dir / "price_old.json"
    latest = config.cache_dir / "price_latest.json"
    older.write_text(json.dumps([{"coin_id": "old"}]))
    latest.write_text(json.dumps([{"coin_id": "new"}]))
    os.utime(older, (100, 100))
    os.utime(latest, (200, 200))
    monkeypatch.setattr(
        utils,
        "get_markets",
        lambda *args, **kwargs: pytest.fail("Existing price cache should be used"),
    )

    assert utils.get_coingecko_markets(type="price", config=config, log=logger) == [
        {"coin_id": "new"}
    ]


def test_api_failure_returns_none_without_creating_cache(
    monkeypatch, config, logger, holdings
):
    monkeypatch.setattr(utils, "get_markets", lambda *args, **kwargs: None)

    assert utils.get_coingecko_markets(config=config, log=logger) is None
    assert list(config.cache_dir.iterdir()) == []


def test_empty_api_response_is_cached_as_an_empty_list(
    monkeypatch, config, logger, holdings
):
    monkeypatch.setattr(utils, "get_markets", lambda *args, **kwargs: [])

    assert utils.get_coingecko_markets(config=config, log=logger) == []
    assert json.loads((config.cache_dir / "markets.json").read_text()) == []


def test_invalid_type_raises_value_error(config, logger):
    with pytest.raises(ValueError, match="Unsupported market cache type"):
        utils.get_coingecko_markets(type="unknown", config=config, log=logger)


@pytest.mark.parametrize(
    "contents",
    [
        "{invalid json",
        '{"id": "bitcoin"}',
        '[{"id": "bitcoin"}, null]',
    ],
)
def test_invalid_cache_contents_are_reported(config, logger, contents):
    (config.cache_dir / "markets.json").write_text(contents)

    with pytest.raises((json.JSONDecodeError, ValueError)):
        utils.get_coingecko_markets(config=config, log=logger)
