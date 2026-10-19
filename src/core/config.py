"src/core"

from pathlib import Path

BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / "data"
FINAL_DIR = DATA_DIR / "final"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

LOG_DIR = BASE_DIR / "logs"


WATCHLIST = [
    {
        "coin_id": "bitcoin",
        "ticker": "BTC",
        "category": "Layer1",
        "quantity_held": 0.45,
        "avg_purchase_price_usd": 38000.00,
    },
    {
        "coin_id": "ethereum",
        "ticker": "eth",
        "category": "Layer1",
        "quantity_held": 6.2,
        "avg_purchase_price_usd": 2200.00,
    },  # lowercase ticker — inconsistent casing
    {
        "coin_id": "solana",
        "ticker": "SOL",
        "category": "Layer1",
        "quantity_held": 120,
        "avg_purchase_price_usd": "",
    },  # missing purchase price
    {
        "coin_id": "cardano",
        "ticker": "ADA",
        "category": "layer1",
        "quantity_held": 5000,
        "avg_purchase_price_usd": 0.38,
    },  # inconsistent category casing
    {
        "coin_id": "ripple",
        "ticker": "XRP",
        "category": "Payments",
        "quantity_held": 8000,
        "avg_purchase_price_usd": 0.55,
    },
    {
        "coin_id": "dogecoin",
        "ticker": "DOGE",
        "category": "Meme",
        "quantity_held": -1500,
        "avg_purchase_price_usd": 0.08,
    },  # invalid negative quantity
    {
        "coin_id": "chainlink",
        "ticker": "LINK",
        "category": "Oracle",
        "quantity_held": 300,
        "avg_purchase_price_usd": 14.50,
    },
    {
        "coin_id": "polkadot",
        "ticker": "DOT",
        "category": "Layer1",
        "quantity_held": 900,
        "avg_purchase_price_usd": 6.80,
    },
    {
        "coin_id": "litecoin",
        "ticker": "LTC",
        "category": "Payments",
        "quantity_held": 40,
        "avg_purchase_price_usd": 72.00,
    },
    {
        "coin_id": "avalanche-2",
        "ticker": "AVAX",
        "category": "Layer1",
        "quantity_held": 150,
        "avg_purchase_price_usd": 28.00,
    },
    {
        "coin_id": "bitcoin",
        "ticker": "BTC",
        "category": "Layer1",
        "quantity_held": 0.45,
        "avg_purchase_price_usd": 38000.00,
    },  # duplicate row (client pasted twice)
    {
        "coin_id": "shiba-inu-typo",
        "ticker": "SHIB",
        "category": "Meme",
        "quantity_held": 900000,
        "avg_purchase_price_usd": 0.00002,
    },  # intentionally bad coin_id — API will 404 on this
]


print(BASE_DIR)
