import logging

import pandas as pd


def inspect_watchlist_data(
    df: pd.DataFrame, log: logging.Logger, label: str = "DataFrame"
) -> list[str]:
    if df is None:
        log.error("Watchlist DataFrame not found!")
        return

    report: list[str] = []

    divider = "=" * 65
    report.append(f"\n{divider}")
    report.append(f"\nINSPECTION REPORT - {label.upper()}")
    report.append(f"\n{divider}\n")

    # Shape
    report.append("Shape\n")
    report.append(f"    {df.shape[0]:,} rows x {df.shape[1]} columns\n")

    # Column names: spot issues immediate issues (wrong names, exta space, inconsistent casing etc)
    report.append("\nColumns:\n")
    for col in df.columns:
        report.append(f"    {col}\n")

    # Data types: check and identify wrong data types
    report.append("\nData Types:\n")
    report.append(f"{df.dtypes.to_string()}\n")

    # Missing values
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / len(df) * 100).round(1)
    missing_df = pd.DataFrame({"count": missing_count, "%": missing_pct})
    actual_missing = missing_df[missing_df["count"] > 0]
    report.append("\nMissing Values: \n")
    if actual_missing.empty:
        report.append("   None - all columns complete\n")
    else:
        report.append(f"{actual_missing.to_string()}\n")

    # Numeric summary - catch negative values, outliers, impossible data etc
    numeric_cols = df.select_dtypes(include="number")
    if not numeric_cols.empty:
        report.append("\nNumeric Summary: \n")
        report.append(f"{df.describe().to_string()}\n")

    # Duplicate rows
    dup_count = df.duplicated().sum()
    report.append(f"\nDuplicate Rows: {dup_count}\n")

    # sample always look at actual data
    report.append("\nFirst 5 Rows: \n")
    report.append(df.head(5).to_string())

    report.append(f"\n{divider}\n")
    

    return report
