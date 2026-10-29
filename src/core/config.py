"src/core"

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# =====================================
# DIRECTORIES AND FILE PATH
# =====================================
BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / "data"
FINAL_DIR = DATA_DIR / "final"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
LOG_DIR = BASE_DIR / "logs"
REPORT_DIR = BASE_DIR / "reports"

# PRIORITY FILE PATH
RAW_WATCHLIST_HOLDING_FILEPATH = RAW_DIR / "watchlist.csv"
TRACKER_LOG_FILEPATH = LOG_DIR / "tracker.log"


# ====================================
# WATCHLIST HOLDING
# ====================================
@dataclass
class Columns:
    coin_id: str = "coin_id"
    ticker: str = "ticker"
    category: str = "category"
    quantity: str = "quantity_held"
    avg_purchase: str = "avg_purchase_price_usd"

    valid_categories: list[str] = field(
        default_factory=lambda: ["Layer 1", "Meme", "Payments", "Oracle"]
    )

    # required columns
    @property
    def required_columns(self) -> list[str]:
        return [
            self.coin_id,
            self.ticker,
            self.category,
            self.quantity,
            self.avg_purchase,
        ]


# =========================================
# COINGECKO CLIENT
# =========================================
@dataclass
class Coingecko:
    base_url: str = "http://api.coingecko.com/api/v3"
    api_key: str = os.getenv("COINGECKO_API_KEY", "")

    # rate limit config
    min_second_api_key: float = 0.7
    min_second_public: float = 2.1
    max_retries: int = 3
    backoff_base_seconds: int = 2  # 2s, 4s, 8s on successive retries


# ========================================
#  PORTFOLIO TRACKER CONFIG
# ========================================
@dataclass
class TrackerConfig:
    """
    Central configuration for the ETL tracker pipeline.
    """

    env: str = "development"  # "development", production" or "staging"

    # dir path
    data_dir: Path = DATA_DIR
    final_dir: Path = FINAL_DIR
    processed_dir: Path = PROCESSED_DIR
    raw_dir: Path = RAW_DIR
    log_dir: Path = LOG_DIR
    report_dir: Path = REPORT_DIR

    # file name
    watchlist_filename: str = "watchlist.csv"

    # watchlist holding
    columns: Columns = field(default_factory=Columns)
    label: str = "Watchlist"

    # output validation
    output_format: str = "csv"  # "csv", "json" or "xlsx"
    skip_validation: bool = False

    # Validation threshold
    max_missing_rate: float = 0.10  # Fail if >10% for critical column missing
    min_rows_expected: int = 12  # Fail if if the output is lesser than this
    quantity_must_be_positive: bool = True  # Fail if quantity is negative

    def __post_init__(self):
        """Create output directories on init."""
        for d in [self.processed_dir, self.final_dir, self.report_dir, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)

    @property
    def raw_watchlist_filepath(self) -> Path:
        return self.raw_dir / self.watchlist_filename


# ================================================
# WATCHLIST SIMULATION DATA
# ================================================
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
