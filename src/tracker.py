from src.cleaning.cleaner import clean_watchlist
from src.core.config import LOG_DIR, RAW_WATCHLIST_HOLDING_FILEPATH, TrackerConfig
from src.core.logger import setup_logging
from src.ingestion.loader import load_watchlist_holding
from src.reporter import generate_flag_report, generate_validation_report, print_reports
from src.validation.check_report import QualityReport
from src.validation.inspector import inspect_watchlist_data
from src.validation.validator import validate_watchlist


def main():
    log = setup_logging(LOG_DIR)
    report = QualityReport()
    config = TrackerConfig()

    log.info("CoinWatch Portfolio Tracker started")

    # load watchlist data
    watchlist_df = load_watchlist_holding(RAW_WATCHLIST_HOLDING_FILEPATH, log)

    # Inspect and validate watchlist holding
    ins_report = inspect_watchlist_data(watchlist_df, log)
    is_validated = validate_watchlist(watchlist_df, config, report, log)

    clean_df = clean_watchlist(watchlist_df, config)

    is_cleaned = validate_watchlist(clean_df, config, report, log)

    # generate and print reports
    is_valid, val_report = generate_validation_report(report, log)
    is_flagged, flag_report = generate_flag_report(report, log)

    # print all report
    print_reports(ins_report, val_report, flag_report, log)
