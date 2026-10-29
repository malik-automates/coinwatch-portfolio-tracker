import logging
from datetime import datetime

import pandas as pd

from src.core.config import REPORT_DIR
from src.validation.check_report import QualityReport

# file timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def write_inspection_report(report: list[str], log: logging.Logger):
    if report is None:
        log.info("Report data to inspect not found!")
        return
    try:
        inspection_report_filepath = REPORT_DIR / f"inspection_report_{timestamp}.txt"
        with open(inspection_report_filepath, "w", encoding="utf-8") as file:
            file.writelines(line for line in report)
    except Exception as e:
        log.error({e})
    log.info("Inspection report generated. check: '%s'", inspection_report_filepath)


def generate_validation_report(
    report: QualityReport, log: logging.Logger
) -> tuple[bool, str]:
    issues = report.issues_found
    if issues is None:
        msg = "No issues found - Validation check passed successfully!"
        log.info(msg)
        return (True, msg)
    try:
        issue_data = []
        for issue in issues:
            issue_data.append(
                {
                    "Issue": issue["description"],
                    "Frequency": issue["count"],
                }
            )
        issue_report = pd.DataFrame(issue_data).to_string(header=True, justify="left")
        return False, issue_report
    except Exception as e:
        log.error("%s", e)
        return (False, f"{e}")


def generate_flag_report(
    report: QualityReport, log: logging.Logger
) -> tuple[bool, str]:
    flags = report.flags
    if flags is None:
        msg = "No data flags found - Validation check passed successfully!"
        log.info(msg)
        return True, msg
    try:
        flag_data = []
        for flag in flags:
            flag_data.append(
                {
                    "Coin": flag["coin_id"],
                    "Flag": flag["flag_type"],
                    "Severity": flag["severity"],
                    "Description": flag["description"],
                }
            )
        flag_report = pd.DataFrame(flag_data).to_string(header=True, justify="left")
        return False, flag_report
    except Exception as e:
        log.error("%s", e)
        return False, f"{e}"


def print_reports(
    ins_report: list[str], val_report: str, flag_report: str, log: logging.Logger
):
    write_inspection_report(ins_report, log)

    # print report to file
    val_report_filepath = REPORT_DIR / f"validation_report_{timestamp}.txt"
    val_report_filepath.write_text(val_report, encoding="utf-8")
    log.info(
        "Validation report gennerated successfully! Check '%s'", val_report_filepath
    )

    # print flag report to file
    flag_report_filepath = REPORT_DIR / f"flag_report_{timestamp}.txt"
    flag_report_filepath.write_text(flag_report, encoding="utf-8")
    log.info("Flag report generated successfully! Check '%s'", flag_report_filepath)
