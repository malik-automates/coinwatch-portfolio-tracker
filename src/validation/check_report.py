# ─────────────────────────────────────────────────────────────────────────────
# DATA QUALITY REPORT
# A structured record of what was found and fixed.
# ─────────────────────────────────────────────────────────────────────────────

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class QualityReport:
    """Tracks data quality findings throughout the pipeline run."""

    run_timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    source_row_count: int = 0
    output_row_count: int = 0
    rows_dropped: int = 0
    issues_found: list[dict[str, str | int]] = field(default_factory=list)
    issues_fixed: list[dict] = field(default_factory=list)
    flags: list[dict[str, str]] = field(default_factory=list)
    validation_passed: bool = True

    def add_issue(
        self,
        description: str,
        count: int,
        fixed: bool = False,
    ) -> None:
        entry = {
            "description": description,
            "count": count,
        }
        if fixed:
            self.issues_fixed.append(entry)
        else:
            self.issues_found.append(entry)

    def add_flag(
        self, coin_id: str, flag: str, severity: str, description: str
    ) -> None:
        entry = {
            "coin_id": coin_id,
            "flag_type": flag,
            "severity": severity,
            "description": description,
        }
        self.flags.append(entry)

    def to_dict(self) -> dict:
        return {
            "run_timestamp": self.run_timestamp,
            "source_row_count": self.source_row_count,
            "output_row_count": self.output_row_count,
            "rows_dropped": self.rows_dropped,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "validation_passed": self.validation_passed,
        }
