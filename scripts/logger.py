"""
Shared logging module for AI Contracts POC.
Import at the top of every script:
    from logger import get_logger
    logger = get_logger(__name__)
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import openpyxl

LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# One timestamped log file per pipeline run (set at process start)
_RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOGS_DIR / f"pipeline_{_RUN_TIMESTAMP}.log"
LATEST_LOG = LOGS_DIR / "pipeline_latest.log"
SUMMARY_XLSX = LOGS_DIR / "pipeline_log_summary.xlsx"


def get_logger(name: str) -> logging.Logger:
    """Returns a logger that writes to console + timestamped file + latest file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (INFO and above)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler — timestamped (DEBUG and above, captures everything)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # File handler — latest.log (always overwritten, for quick inspection)
    lh = logging.FileHandler(LATEST_LOG, mode="w", encoding="utf-8")
    lh.setLevel(logging.DEBUG)
    lh.setFormatter(fmt)
    logger.addHandler(lh)

    return logger


def write_summary_xlsx(events: list) -> None:
    """
    Writes or appends to pipeline_log_summary.xlsx.
    events = list of dicts with keys:
        run_timestamp, script, contract_id, level, message
    Call this at the end of each script with all WARNING/ERROR events.
    """
    if not events:
        return

    headers = ["Run Timestamp", "Script", "Contract ID", "Level", "Message"]

    if SUMMARY_XLSX.exists():
        wb = openpyxl.load_workbook(SUMMARY_XLSX)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Log Summary"
        ws.append(headers)

    for event in events:
        ws.append([
            event.get("run_timestamp", _RUN_TIMESTAMP),
            event.get("script", ""),
            event.get("contract_id", ""),
            event.get("level", ""),
            event.get("message", ""),
        ])

    wb.save(SUMMARY_XLSX)
