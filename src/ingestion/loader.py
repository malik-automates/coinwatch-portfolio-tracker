import logging
from pathlib import Path

import pandas as pd


def load_watchlist_holding(filepath: Path, log: logging.Logger) -> pd.DataFrame:
    """load watchlist holding to either csv or excel file"""
    df = ""

    def log_df_info(ext: str, df: pd.DataFrame, filepath: Path):
        log.info(
            "Loaded %d rows x %d cols from '%s'.'%s'", *df.shape, filepath.name, ext
        )

    if filepath.suffix == ".csv":
        df = pd.read_csv(
            filepath,
            dtype={"coin_id": "string", "ticker": "string", "category": "string"},
            na_values=["", "N/A", "NULL", "null", "nan", "none"],
            low_memory=False,
        )
        log_df_info("csv", df, filepath)
        return df
    elif filepath.suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(filepath, index_col=False)
        log_df_info("excel", df, filepath)
        return df
    else:
        raise ValueError("Invalid watchlist file! File should be either CSV or Excel")
