import logging

import pandas as pd

from src.core.config import TrackerConfig
from src.validation.check_report import QualityReport


def validate_watchlist(
    watchlist_df: pd.DataFrame,
    config: TrackerConfig,
    report: QualityReport,
    log: logging.Logger,
    label: str = "watchlist",
) -> bool:
    """
    Validate raw data against quality rules.

    Returns:
        True if validation passes, False if pipeline should stop.
    """
    log.info("── VALIDATE ─────────────────────────────────────────")
    passed = True

    # ── Rule 1: Required columns must exist ───────────────────────────────
    required_cols = config.columns.required_columns
    missing_cols = [col for col in required_cols if col not in watchlist_df.columns]
    if missing_cols:
        log.error("VALIDATION FAILED: Missing required columns: %s", missing_cols)
        report.add_issue(f"Missing Columns: {missing_cols}", len(missing_cols))
        passed = False
    else:
        log.info("All required columns present.")

    # ── Rule 2: Minimum row count ─────────────────────────────────────────
    row_count = len(watchlist_df)
    if row_count < config.min_rows_expected:
        log.error(
            "VALIDATION FAIL: Only %d rows — expected at least %d",
            len(watchlist_df),
            config.min_rows_expected,
        )
        report.add_issue(
            f"Row count {len(watchlist_df)} below minimum {config.min_rows_expected}", 1
        )
        passed = False
    else:
        log.info("✓ Row count check passed: %d rows", len(watchlist_df))

    # ── Rule 3: Missing values in critical columns ───────────────────────────────
    critical_cols = config.columns.required_columns
    for col in critical_cols:
        if col not in watchlist_df.columns:
            continue
        if col == config.columns.coin_id:
            null_count = watchlist_df[col].isnull().sum()
            if null_count > 0:
                log.error("VALIDATION FAIL: '%s' must not have missing values!")
                passed = False
                return passed
        missing_count = watchlist_df[col].isna().sum()
        missing_rate = missing_count / len(watchlist_df)
        if missing_rate > config.max_missing_rate:
            log.error(
                "VALIDATION FAIL: '%s' is %.1f%% missing (threshold: %.1f%%)",
                col,
                missing_rate * 100,
                config.max_missing_rate * 100,
            )
            report.add_issue(
                f"Columnn {col} exceed missing threshold: {missing_rate:.1%}",
                missing_count,
            )
            passed = False
        elif missing_count > 0:
            log.warning(
                "'%s' has %d missing values (%.1f%%)",
                col,
                missing_count,
                missing_rate * 100,
            )
            report.add_issue(f"{col} has missing value", missing_count)
            passed = False
            col_na_df = watchlist_df.loc[watchlist_df[col].isna()]
            for idx in col_na_df.index:
                coin_id = watchlist_df.loc[idx, config.columns.coin_id]
                report.add_flag(
                    str(coin_id), "MISSING_VALUE", "MEDIUM", f"{col} has missing value"
                )
        else:
            log.info("'%s' has 'No Missing Values' - check passed!", col)

    # ── Rule 4: Duplicate coin IDs ───────────────────────────────────────
    dup_coin_df = watchlist_df.loc[watchlist_df[config.columns.coin_id].duplicated()]
    dup_count = len(dup_coin_df)
    if dup_count > 0:
        log.warning("Found %d duplicate entry", dup_count)
        report.add_issue(
            f"{coin_id} has Duplicate Entry",
            dup_count,
        )
        passed = False
        for idx in dup_coin_df.index:
            coin_id = dup_coin_df.loc[idx, config.columns.coin_id]
            report.add_flag(
                str(coin_id),
                "DUPLICATE_ENTRY",
                "MEDIUM",
                f"{coin_id} has Duplicate Entry",
            )
    else:
        log.info("No duplicat found - check passed!")

    # ── Rule 5: Valid category values ───────────────────────────────────────
    valid_categories = set(config.valid_categories)
    actual_categories = (
        watchlist_df[config.columns.category]
        .str.strip()
        .str.capitalize()
        .dropna()
        .unique()
    )
    invalid_categories = set(actual_categories) - valid_categories
    if invalid_categories:
        count = (
            watchlist_df[config.columns.category]
            .str.capitalize()
            .str.strip()
            .isin(invalid_categories)
            .sum()
        )
        log.warning(
            "%d Unrecognised category values found: %s", count, invalid_categories
        )
        report.add_issue(f"Unrecognised category values: {invalid_categories}", count)
        passed = False
    else:
        log.info("All Categories are VALID!")

    # ── Rule 6: Negative quantity ───────────────────────────────────────
    negative_qty = watchlist_df.loc[
        watchlist_df[config.columns.quantity] < 0, config.columns.quantity
    ]
    negative_qty_count = len(negative_qty)
    if negative_qty_count > 0:
        log.warning("'%d' Negative quantity values found", negative_qty_count)
        report.add_issue(
            f"Negative quantity: '{negative_qty_count}' found", negative_qty_count
        )
        passed = False
        for idx in negative_qty.index:
            coin_id = watchlist_df.loc[idx, config.columns.coin_id]
            report.add_flag(
                str(coin_id),
                "NEGATIVE_QUANTITY",
                "MEDIUM",
                f"{config.columns.quantity} has Negative value",
            )
    else:
        log.info("No Negative quantity found - check passed")

    # ── Rule 7: Inconsistent ticker casing ───────────────────────────────────────
    ticker_df = watchlist_df[config.columns.ticker]
    not_uppercases = [v for v in ticker_df.values if v.strip() != v.strip().upper()]
    if len(not_uppercases) > 0:
        log.warning(
            "Found %d inconsistent ticker casing: %s",
            len(not_uppercases),
            not_uppercases,
        )
        report.add_issue(
            f"Inconsistent Ticker casing: {len(not_uppercases)} found",
            len(not_uppercases),
        )
        passed = False
    else:
        log.info("No inconsistent ticker casing found - check passed!")

    report.validation_passed = passed

    if passed and label == "watchlist":
        log.info("✅ Validation Passed - Proceeed to fetch Coingecko market")
    elif passed and label == "coingecko":
        log.info("Validation Passed - Proceed for watchlist holding calculations")
    else:
        log.error("✗ Validation FAILED — check quality report before rerunning")

    return passed
