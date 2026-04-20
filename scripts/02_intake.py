"""
scripts/02_intake.py

Scans contracts/ and mock_contracts/ for .pdf and .docx files, assigns ContractIDs,
and writes outputs/contract_catalog.xlsx.

Usage: python scripts/02_intake.py
"""
import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from logger import get_logger, write_summary_xlsx, _RUN_TIMESTAMP

# Allow running from project root or scripts/
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import config

import openpyxl

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
CTR_ID_PATTERN = re.compile(r"^(CTR-\d+)", re.IGNORECASE)


def collect_files() -> list[dict]:
    """
    Walk contracts/ first, then mock_contracts/ if contracts/ is empty or has no matches.
    Returns list of dicts with keys: filename, filepath, filetype.
    """
    files = []

    # Primary: contracts/
    config.CONTRACTS_DIR.mkdir(exist_ok=True)
    for f in sorted(config.CONTRACTS_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append({"filename": f.name, "filepath": str(f), "filetype": f.suffix.lower().lstrip(".")})

    # Fallback: mock_contracts/ (used when no real contracts are present)
    config.MOCK_CONTRACTS_DIR.mkdir(exist_ok=True)
    mock_files = [
        f for f in sorted(config.MOCK_CONTRACTS_DIR.iterdir())
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files and mock_files:
        logger.info(f"  contracts/ is empty — using {len(mock_files)} files from mock_contracts/")
        for f in mock_files:
            files.append({"filename": f.name, "filepath": str(f), "filetype": f.suffix.lower().lstrip(".")})
    elif mock_files:
        logger.info(f"  Found {len(files)} file(s) in contracts/ and {len(mock_files)} in mock_contracts/ — using both")
        for f in mock_files:
            files.append({"filename": f.name, "filepath": str(f), "filetype": f.suffix.lower().lstrip(".")})

    return files


def assign_contract_id(filename: str, existing_ids: set, next_counter: list) -> str:
    """
    If the filename starts with CTR-NNN, use that ID (avoids re-assigning mock IDs).
    Otherwise assign the next sequential CTR-NNN not already in use.
    """
    match = CTR_ID_PATTERN.match(filename)
    if match:
        cid = match.group(1).upper()
        if cid not in existing_ids:
            return cid
        # Already used (duplicate filename edge case) — fall through to assign new

    while True:
        cid = f"CTR-{next_counter[0]:03d}"
        next_counter[0] += 1
        if cid not in existing_ids:
            return cid


def write_catalog(rows: list[dict]) -> None:
    config.OUTPUTS_DIR.mkdir(exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Catalog"

    headers = ["ContractID", "FileName", "FilePath", "FileType", "IntakeTimestamp"]
    ws.append(headers)

    for row in rows:
        ws.append([
            row["contract_id"],
            row["filename"],
            row["filepath"],
            row["filetype"],
            row["intake_timestamp"],
        ])

    # Auto-fit column widths (approximate)
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 80)

    wb.save(config.CONTRACT_CATALOG_XLSX)
    logger.info(f"  Catalog written to {config.CONTRACT_CATALOG_XLSX}")


def main():
    summary_events = []
    logger.info("[STEP 1] Starting contract intake")

    files = collect_files()
    if not files:
        logger.warning("No .pdf or .docx files found in contracts/ or mock_contracts/")
        summary_events.append({
            "run_timestamp": _RUN_TIMESTAMP,
            "script": "02_intake",
            "contract_id": "",
            "level": "WARNING",
            "message": "No .pdf or .docx files found in contracts/ or mock_contracts/",
        })
        write_summary_xlsx(summary_events)
        return

    logger.info(f"  Found {len(files)} file(s) to catalog")

    existing_ids: set = set()
    next_counter = [1]
    intake_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []

    for f in files:
        cid = assign_contract_id(f["filename"], existing_ids, next_counter)
        existing_ids.add(cid)
        rows.append({
            "contract_id": cid,
            "filename": f["filename"],
            "filepath": f["filepath"],
            "filetype": f["filetype"],
            "intake_timestamp": intake_ts,
        })
        logger.info(f"  {cid} <- {f['filename']}")

    write_catalog(rows)
    logger.info(f"[STEP 1] Complete -- {len(rows)} contracts cataloged -> {config.CONTRACT_CATALOG_XLSX}")
    write_summary_xlsx(summary_events)


if __name__ == "__main__":
    main()
