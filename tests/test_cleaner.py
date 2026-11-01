import pandas as pd
from pandas.testing import assert_frame_equal

from src.cleaning.cleaner import clean_watchlist
from src.core.config import TrackerConfig


def _config(tmp_path):
    return TrackerConfig(
        data_dir=tmp_path / "data",
        final_dir=tmp_path / "final",
        processed_dir=tmp_path / "processed",
        raw_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        report_dir=tmp_path / "reports",
    )


def test_clean_watchlist_applies_all_cleaning_steps_and_preserves_input(tmp_path):
    watchlist = pd.DataFrame(
        [
            {
                "coin_id": "bitcoin",
                "ticker": "btc",
                "category": "Layer1",
                "quantity_held": 0.45,
                "avg_purchase_price_usd": None,
            },
            {
                "coin_id": "bitcoin",
                "ticker": "BTC",
                "category": "Meme",
                "quantity_held": 10,
                "avg_purchase_price_usd": 250,
            },
            {
                "coin_id": "ethereum",
                "ticker": "eth",
                "category": "payments",
                "quantity_held": -2,
                "avg_purchase_price_usd": 1000,
            },
        ]
    )
    original = watchlist.copy(deep=True)

    cleaned = clean_watchlist(watchlist, _config(tmp_path))

    expected = pd.DataFrame(
        [
            {
                "coin_id": "bitcoin",
                "ticker": "BTC",
                "category": "Layer 1",
                "quantity_held": 0.45,
                "avg_purchase_price_usd": "None",
            },
            {
                "coin_id": "ethereum",
                "ticker": "ETH",
                "category": "Payments",
                "quantity_held": 0.0,
                "avg_purchase_price_usd": 1000.0,
            },
        ]
    )

    assert_frame_equal(cleaned, expected)
    assert_frame_equal(watchlist, original)
