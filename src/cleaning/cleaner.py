import pandas as pd

from src.core.config import TrackerConfig


def clean_watchlist(watchlist_df: pd.DataFrame, config: TrackerConfig) -> pd.DataFrame:
    df = dedup(watchlist_df, config)
    df = handle_missing_value(df, config)
    df = handle_negative_qty(df, config)
    df = normalize_category(df, config)
    df = normalize_ticker(df, config)
    return df


# handle missing cost for avg_purchase_price column
# set it to None
def handle_missing_value(df: pd.DataFrame, config: TrackerConfig) -> pd.DataFrame:
    df = df.copy()
    # target the affected columns
    df[config.columns.avg_purchase] = df[config.columns.avg_purchase].fillna("None")
    return df


# Normalize ticker casing
# set all categories to uppercase
def normalize_ticker(df: pd.DataFrame, config: TrackerConfig) -> pd.DataFrame:
    df = df.copy()
    df[config.columns.ticker] = df[config.columns.ticker].str.upper()
    return df


# handle duplicate coin_id
# keep first and remove others
def dedup(df: pd.DataFrame, config: TrackerConfig) -> pd.DataFrame:
    df = df.copy()
    duplicate_mask = df.duplicated(subset=[config.columns.coin_id], keep="first")
    df = df[~duplicate_mask].reset_index(drop=True)
    return df


# handle negative quantity
# set it to 0
def handle_negative_qty(df: pd.DataFrame, config: TrackerConfig) -> pd.DataFrame:
    df = df.copy()
    df[config.columns.quantity] = df[config.columns.quantity].apply(
        lambda x: 0 if x < 1 else x
    )
    return df


# handle unrecognize category
def normalize_category(df: pd.DataFrame, config: TrackerConfig) -> pd.DataFrame:
    df = df.copy()
    df[config.columns.category] = (
        df[config.columns.category]
        .str.replace("layer1", "Layer 1", case=False)
        .str.title()
    )
    return df
