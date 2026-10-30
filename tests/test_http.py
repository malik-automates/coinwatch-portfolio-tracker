import logging

import pytest
import requests

from src.api_client.coingecko import http


def test_get_api_key_returns_key(monkeypatch):
    monkeypatch.setattr(http.cg_api, "api_key", "demo-key")

    assert http.get_api_key(logging.getLogger("test.http")) == "demo-key"


def test_get_api_key_warns_when_key_is_missing(monkeypatch, caplog):
    monkeypatch.setattr(http.cg_api, "api_key", "")
    logger = logging.getLogger("test.http")

    with caplog.at_level(logging.WARNING, logger="test.http"):
        result = http.get_api_key(logger)

    assert result is None
    assert "falling back to the public" in caplog.text


def test_retry_action_retries_connection_error_then_returns_value(monkeypatch):
    monkeypatch.setattr(http, "_throttle", lambda: None)
    sleeps = []
    monkeypatch.setattr(http.time, "sleep", sleeps.append)
    calls = 0

    def action():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise requests.ConnectionError("connection lost")
        return "ok"

    result = http.retry_action(
        action,
        log=logging.getLogger("test.http"),
        retries=3,
        backoff_base=0.25,
    )

    assert result == "ok"
    assert calls == 2
    assert sleeps == [0.25]


def test_retry_action_raises_after_all_attempts(monkeypatch, caplog):
    monkeypatch.setattr(http, "_throttle", lambda: None)
    sleeps = []
    monkeypatch.setattr(http.time, "sleep", sleeps.append)
    logger = logging.getLogger("test.http")

    with caplog.at_level(logging.ERROR, logger="test.http"):  # noqa: SIM117
        with pytest.raises(requests.Timeout, match="timed out"):
            http.retry_action(
                lambda: (_ for _ in ()).throw(requests.Timeout("timed out")),
                log=logger,
                retries=3,
                backoff_base=0.5,
            )

    assert sleeps == [0.5, 1.0]
    assert "failed after 3 attempts" in caplog.text


def test_throttle_waits_only_for_remaining_interval(monkeypatch):
    times = iter([10.2, 10.2])
    sleeps = []
    monkeypatch.setattr(http.time, "time", lambda: next(times))
    monkeypatch.setattr(http.time, "sleep", sleeps.append)
    monkeypatch.setattr(http.cg_api, "api_key", "demo-key")
    monkeypatch.setattr(http.cg_api, "min_second_api_key", 0.7)
    monkeypatch.setattr(http, "_last_call_time", 10.0)

    http._throttle()

    assert sleeps == pytest.approx([0.5])
    assert http._last_call_time == 10.2
