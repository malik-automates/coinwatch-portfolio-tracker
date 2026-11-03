import logging

import pandas as pd

from src.core.config import TrackerConfig
from src.validation import validator
from src.validation.check_report import QualityReport


def _config(tmp_path):
    return TrackerConfig(
        data_dir=tmp_path / "data",
        final_dir=tmp_path / "final",
        processed_dir=tmp_path / "processed",
        raw_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        report_dir=tmp_path / "reports",
        min_rows_expected=1,
    )


def _watchlist():
    return pd.DataFrame(
        [
            {
                "coin_id": "bitcoin",
                "ticker": "BTC",
                "category": "Layer 1",
                "quantity_held": 1,
                "avg_purchase_price_usd": 100,
            },
            {
                "coin_id": "unknown-coin",
                "ticker": "UNKNOWN",
                "category": "Meme",
                "quantity_held": 1,
                "avg_purchase_price_usd": 100,
            },
        ]
    )


def test_validate_watchlist_flags_coin_ids_missing_from_coingecko(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        validator,
        "get_coingecko_markets",
        lambda **kwargs: [{"id": "bitcoin", "symbol": "btc"}],
    )
    report = QualityReport()

    passed = validator.validate_watchlist(
        _watchlist(), _config(tmp_path), report, logging.getLogger("test.validator")
    )

    assert passed is True
    assert [flag["coin_id"] for flag in report.flags] == ["unknown-coin"]
    assert report.flags[0]["flag_type"] == "API_ERROR_404"


def test_validate_watchlist_skips_coin_id_flags_if_coingecko_unavailable(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(validator, "get_coingecko_markets", lambda **kwargs: None)
    report = QualityReport()

    passed = validator.validate_watchlist(
        _watchlist(), _config(tmp_path), report, logging.getLogger("test.validator")
    )

    assert passed is True
    assert report.flags == []
