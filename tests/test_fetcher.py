import json
import logging

import requests

from src.api_client.coingecko import fetcher, http
from src.core.config import Coingecko, TrackerConfig


def _response(status_code: int, payload: object) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response._content = json.dumps(payload).encode()
    return response


def _config(tmp_path) -> TrackerConfig:
    return TrackerConfig(
        data_dir=tmp_path / "data",
        final_dir=tmp_path / "final",
        processed_dir=tmp_path / "processed",
        raw_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        report_dir=tmp_path / "reports",
        coingecko=Coingecko(
            base_url="https://api.example.test/v3",
            max_retries=2,
            backoff_base_seconds=0,
        ),
    )


def test_get_markets_passes_expected_request_arguments(monkeypatch, tmp_path):
    captured = {}

    def fake_get(url, *, params, timeout):
        captured.update(url=url, params=params, timeout=timeout)
        return _response(200, [{"id": "bitcoin", "current_price": 65000}])

    monkeypatch.setattr(fetcher.requests, "get", fake_get)
    monkeypatch.setattr(fetcher, "get_api_key", lambda log: "demo-key")
    monkeypatch.setattr(http, "_throttle", lambda: None)

    result = fetcher.get_markets(
        ["bitcoin", "ethereum"],
        "eur",
        config=_config(tmp_path),
        log=logging.getLogger("test.fetcher"),
    )

    assert result == [{"id": "bitcoin", "current_price": 65000}]
    assert captured == {
        "url": "https://api.example.test/v3/coins/markets",
        "params": {
            "vs_currency": "eur",
            "ids": "bitcoin,ethereum",
            "order": "market_cap_desc",
            "price_change_percentage": "24h, 7d",
            "sparkline": "false",
            "x_cg_demo_api_key": "demo-key",
        },
        "timeout": 15,
    }


def test_get_coin_detail_returns_none_for_not_found(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(
        fetcher.requests,
        "get",
        lambda *args, **kwargs: _response(404, {"error": "missing"}),
    )
    monkeypatch.setattr(fetcher, "get_api_key", lambda log: None)
    monkeypatch.setattr(http, "_throttle", lambda: None)

    result = fetcher.get_coin_detail(
        "unknown-coin",
        _config(tmp_path),
        logging.getLogger("test.fetcher"),
    )

    assert result is None
    assert "Not found (404)" in caplog.text


def test_get_coin_detail_sends_detail_query(monkeypatch, tmp_path):
    captured = {}
    payload = {"id": "ethereum", "market_data": {"current_price": {"usd": 3000}}}

    def fake_get(url, *, params, timeout):
        captured.update(url=url, params=params, timeout=timeout)
        return _response(200, payload)

    monkeypatch.setattr(fetcher.requests, "get", fake_get)
    monkeypatch.setattr(fetcher, "get_api_key", lambda log: None)
    monkeypatch.setattr(http, "_throttle", lambda: None)

    result = fetcher.get_coin_detail(
        "ethereum",
        _config(tmp_path),
        logging.getLogger("test.fetcher"),
    )

    assert result == payload
    assert captured == {
        "url": "https://api.example.test/v3/ethereum",
        "params": {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "true",
            "sparkline": "false",
        },
        "timeout": 15,
    }


def test_get_markets_retries_a_rate_limit_with_a_new_request(monkeypatch, tmp_path):
    responses = iter(
        [
            _response(429, {"error": "rate limited"}),
            _response(200, [{"id": "bitcoin"}]),
        ]
    )
    calls = []

    def fake_get(*args, **kwargs):
        calls.append((args, kwargs))
        return next(responses)

    monkeypatch.setattr(fetcher.requests, "get", fake_get)
    monkeypatch.setattr(fetcher, "get_api_key", lambda log: "demo-key")
    monkeypatch.setattr(http, "_throttle", lambda: None)
    monkeypatch.setattr(http.time, "sleep", lambda seconds: None)

    result = fetcher.get_markets(
        ["bitcoin"],
        config=_config(tmp_path),
        log=logging.getLogger("test.fetcher"),
    )

    assert result == [{"id": "bitcoin"}]
    assert len(calls) == 2


def test_get_coin_details_batch_keeps_results_for_each_coin(monkeypatch, tmp_path):
    responses = iter(
        [
            _response(200, {"id": "bitcoin"}),
            _response(404, {"error": "missing"}),
        ]
    )
    monkeypatch.setattr(
        fetcher.requests,
        "get",
        lambda *args, **kwargs: next(responses),
    )
    monkeypatch.setattr(fetcher, "get_api_key", lambda log: None)
    monkeypatch.setattr(http, "_throttle", lambda: None)

    result = fetcher.get_coin_details_batch(
        ["bitcoin", "unknown-coin"],
        _config(tmp_path),
        logging.getLogger("test.fetcher"),
    )

    assert result == {"bitcoin": {"id": "bitcoin"}, "unknown-coin": None}
