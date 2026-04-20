# AI Contracts POC — Agent-Ready Build Guide (Version 3)

**Owner:** Braden Jones  
**Deadline:** Thursday, April 24, 2026 (EOD)  
**Deliverable:** Working local prototype — runnable pipeline + Excel validation table + Power BI dashboard  
**Builder pattern:** Braden owns architecture decisions; Claude Code writes all code  
**LLM:** LiteLLM (local proxy, already configured, pointed at approved model)  
**Storage:** Excel files (no GCP for POC — IT approval pending)  
**OCR stack:** Python only — `pdfplumber` (text PDFs) + `pytesseract` (scanned/image PDFs)  
**Output channel:** Power BI (existing workspace) + Excel validation file  
**Version control:** Git — single `main` branch, commit after each Claude Code session  
**Logging:** Console + rotating file logs + summary log Excel for non-dev reviewers  
**Docs:** `PROGRESS.md` auto-updated by Claude Code after each session  

---

## 0. How to Use This Guide with Claude Code

**Before touching any code**, run this in your terminal from inside the project folder:

```
cd C:\Users\jonesbrade\Documents\ai-contracts-poc
git init
claude.cmd /plan "Build the AI Contracts POC pipeline as described in AI_Contracts_POC_Build_Guide_v3.md"
```

Claude Code will read this file, write a step-by-step execution plan, and wait for your approval before writing any code. Review the plan, approve it, then let it run. Each phase below maps to a Claude Code task boundary.

**After every Claude Code session**, run:
```
git add .
git commit -m "Session [N]: [brief description of what was built]"
```

Claude Code will also update `PROGRESS.md` automatically at the end of each session.

**Approval checkpoints** (places where you must review before Claude Code proceeds):
- After mock contract generation — verify docs look realistic
- After first extraction run — verify field quality before building rules
- After validation Excel is generated — verify structure before demo
- After Business Entity load file generation — verify format matches Coupa expectations

---

## 1. Project Directory Structure

```
C:\Users\jonesbrade\Documents\ai-contracts-poc\
│
├── .gitignore
├── CLAUDE.md                              # Claude Code session instructions (auto-created)
├── AI_Contracts_POC_Build_Guide_v3.md     # This file
├── PROGRESS.md                            # Auto-updated by Claude Code after each session
├── README.md                              # Setup + run instructions (written in Session 7)
├── requirements.txt
├── config.py
├── schema.json
├── rules.xlsx                             # EDITABLE: Risk rules table
├── run_pipeline.py                        # Master orchestrator (steps 02–07)
│
├── contracts\                             # INPUT: Drop ALL contract docs here (no subfolders)
│   └── [any .pdf or .docx files go here]
│
├── source_data\                           # Manual input files provided by user
│   └── source_business_entities.xlsx     # User-provided BE source file (required for script 00)
│
├── mock_contracts\                        # Auto-generated mock contracts (if no real samples)
│   └── [generated PDFs + docx]
│
├── outputs\                               # ALL pipeline outputs live here
│   ├── contract_catalog.xlsx
│   ├── contract_text\                     # Raw extracted text per contract (.txt)
│   ├── page_maps\                         # Page-level text chunks per contract (.json)
│   ├── extracted_fields.xlsx
│   ├── risk_signals.xlsx
│   ├── summaries.xlsx
│   ├── validation_review.xlsx             # PRIMARY human review artifact
│   ├── coupa_ready.xlsx                   # Generated after human approval (contract header data)
│   └── Target_Business_Entity_Load_File.xlsx  # Coupa BE prerequisite artifact (from script 00)
│
├── logs\                                  # All logs live here
│   ├── pipeline_YYYYMMDD_HHMMSS.log       # Full run log (one file per pipeline run)
│   ├── pipeline_latest.log                # Symlink / copy of most recent log
│   └── pipeline_log_summary.xlsx         # Non-dev readable error summary (auto-updated)
│
└── scripts\
    ├── 00_build_be_load_file.py           # Generate Coupa Business Entity Load File
    ├── 01_generate_mocks.py               # Generate mock contracts if needed
    ├── 02_intake.py                       # Catalog input contracts
    ├── 03_extract_text.py                 # OCR + text extraction
    ├── 04_extract_fields.py               # LiteLLM structured extraction
    ├── 05_run_rules.py                    # Rules engine
    ├── 06_summarize.py                    # Plain-language summaries
    ├── 07_build_validation.py             # Assemble validation_review.xlsx
    ├── 08_coupa_artifact.py               # Generate coupa_ready.xlsx from approved rows
    └── logger.py                          # Shared logging module (imported by all scripts)
```

**Key change from v2:** All contracts go into `contracts\` directly — no `clean\` or `messy\` subfolders. The pipeline handles all files in that one folder regardless of quality.

---

## 2. Git & Version Control Setup

### .gitignore (Claude Code creates this on Session 1)
```
# Python
__pycache__/
*.pyc
*.pyo
.env
venv/
.venv/

# Secrets — never commit
.env.local
secrets.txt
*.key

# Large outputs (too big for git, regenerated by pipeline)
outputs/contract_text/
outputs/page_maps/
mock_contracts/

# Logs (regenerated, no value in git history)
logs/*.log

# OS
.DS_Store
Thumbs.db

# Excel lock files
~$*.xlsx
```

### Commit convention (one commit per Claude Code session)
```
Session 1: Scaffold + mock contracts
Session 2: Intake + text extraction pipeline
Session 3: LLM field extraction
Session 4: Rules engine + summaries
Session 5: Validation table + Coupa artifacts
Session 6: Master orchestrator + Power BI setup
Session 7: Cleanup + README + final PROGRESS.md
```

**Note:** `source_data/source_business_entities.xlsx`, `rules.xlsx`, and all `outputs/*.xlsx` files ARE committed — they are the demo artifacts and should be in version history.

---

## 3. Logging Architecture

### logger.py (shared module imported by every script)

Claude Code must implement this module so all scripts use it consistently.

```python
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

LOGS_DIR = Path(__file__).parent / "logs"
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


def write_summary_xlsx(events: list[dict]) -> None:
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
```

### Logging conventions for all scripts

Every script must:
1. Import `get_logger` and `write_summary_xlsx` from `logger.py`
2. Log `INFO` at start and end of each major step: `[STEP N] Starting...` / `[STEP N] Complete — {n} records`
3. Log `WARNING` for recoverable issues: OCR fallback triggered, low confidence field, rule skipped
4. Log `ERROR` for failures: extraction failed, file unreadable, LLM returned invalid JSON
5. Collect all `WARNING` and `ERROR` events into a list and call `write_summary_xlsx()` before script exits

### pipeline_log_summary.xlsx columns

| Column | Description |
|---|---|
| Run Timestamp | When the pipeline run started (YYYYMMDD_HHMMSS) |
| Script | Which script generated the event |
| Contract ID | ContractID if applicable, blank if not contract-specific |
| Level | WARNING or ERROR |
| Message | Human-readable description of the issue |

This file accumulates across runs so you can see error trends over time. It is safe to delete and regenerate.

---

## 4. PROGRESS.md — Auto-Update Protocol

Claude Code must append to `PROGRESS.md` at the end of every session using this template:

```markdown
## Session [N] — [Date] — [Brief Title]

**What was built:**
- [Bullet list of files created or modified]

**Scripts added:**
- [script name]: [one-line description]

**Key decisions made:**
- [Any architectural choices or deviations from the build guide]

**Known issues / open items:**
- [Anything that needs follow-up or wasn't fully resolved]

**Git commit:** `Session [N]: [commit message]`

---
```

The initial `PROGRESS.md` header (written in Session 1):

```markdown
# AI Contracts POC — Progress Log

**Project:** AI-assisted contract ingestion, extraction, and Coupa staging  
**Owner:** Braden Jones  
**Started:** April 20, 2026  
**Target:** April 24, 2026 (Thursday demo)  
**Guide version:** v3  

---
```

---

## 5. Environment Setup

### requirements.txt
```
pdfplumber>=0.10.0
pytesseract>=0.3.10
python-docx>=1.1.0
openpyxl>=3.1.2
litellm>=1.35.0
Pillow>=10.0.0
pdf2image>=1.16.3
python-dateutil>=2.9.0
tqdm>=4.66.0
reportlab>=4.0.0
```

> **Tesseract install (Windows):** https://github.com/UB-Mannheim/tesseract/wiki  
> After install, set `TESSERACT_PATH` env var or update `config.py`.

### config.py
```python
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# Input directories
CONTRACTS_DIR       = PROJECT_ROOT / "contracts"         # single flat folder — all docs go here
SOURCE_DATA_DIR     = PROJECT_ROOT / "source_data"
MOCK_CONTRACTS_DIR  = PROJECT_ROOT / "mock_contracts"

# Source files (user-provided)
SOURCE_BE_XLSX      = SOURCE_DATA_DIR / "source_business_entities.xlsx"

# Output directory
OUTPUTS_DIR         = PROJECT_ROOT / "outputs"
CONTRACT_TEXT_DIR   = OUTPUTS_DIR / "contract_text"
PAGE_MAPS_DIR       = OUTPUTS_DIR / "page_maps"

# Output Excel files
CONTRACT_CATALOG_XLSX       = OUTPUTS_DIR / "contract_catalog.xlsx"
EXTRACTED_FIELDS_XLSX       = OUTPUTS_DIR / "extracted_fields.xlsx"
RISK_SIGNALS_XLSX           = OUTPUTS_DIR / "risk_signals.xlsx"
SUMMARIES_XLSX              = OUTPUTS_DIR / "summaries.xlsx"
VALIDATION_XLSX             = OUTPUTS_DIR / "validation_review.xlsx"
COUPA_READY_XLSX            = OUTPUTS_DIR / "coupa_ready.xlsx"
BE_LOAD_FILE_XLSX           = OUTPUTS_DIR / "Target_Business_Entity_Load_File.xlsx"

# Rules
RULES_XLSX = PROJECT_ROOT / "rules.xlsx"

# LiteLLM — reads from environment variables, no hardcoded keys
LITELLM_MODEL    = os.environ.get("LITELLM_MODEL",    "gpt-4o")
LITELLM_API_BASE = os.environ.get("LITELLM_API_BASE", "http://localhost:4000")

# Tesseract (Windows)
TESSERACT_PATH = os.environ.get(
    "TESSERACT_PATH",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Pipeline parameters
MAX_TOKENS_EXTRACTION       = 2000
MAX_TOKENS_SUMMARY          = 500
CONFIDENCE_THRESHOLD_WARN   = 0.6
OCR_MIN_TEXT_LENGTH         = 100   # chars; below this triggers pytesseract fallback
```

---

## 6. Script 00 — Business Entity Load File Generator

**Purpose:** Generate the Coupa Business Entity Load File from a user-provided source Excel file. This is a prerequisite step — Business Entities must exist in Coupa before contracts can be uploaded. Run this first, manually upload the output to Coupa, wait for approval, then proceed with contract ingestion.

**Input:** `source_data/source_business_entities.xlsx`  
**Output:** `outputs/Target_Business_Entity_Load_File.xlsx`  
**Trigger:** Run manually before the main pipeline: `python scripts/00_build_be_load_file.py`

---

### 6.1 Target Workbook Structure (exact spec — do not deviate)

The output workbook is named `Target Business Entity Load File` and contains a single worksheet named `Target`.

The sheet must begin with **exactly 5 header rows** in this order:

**Row 1 — Business Entity header (11 columns):**
`Business Entity | ID | Name | Display Name | Type | Status | Country of Origin Code | State of Origin | Formation Type | Business Entity Alternate Names | Parent Business Entity Id`

**Row 2 — Contact header (9 columns):**
`Contact | ID | Primary | Email | Name Given | Name Family | Phone Work | Phone Mobile | Phone Fax`

**Row 3 — Address header (13 columns):**
`Address | Id | Primary | Name | Line 1 | Line 2 | Line 3 | Line 4 | City | State | Postal Code | Country Code | Plant`

**Row 4 — Business Entity External Reference header (5 columns):**
`Business Entity External Reference | ID | Name | Type | Value`

**Row 5 — Supplier Sharing Setting header (6 columns):**
`Supplier Sharing Setting | ID | Sharable ID | Sharable Type | Shared Category | Share with Children`

> Row 5 is a header-only row. No data rows are ever created for Supplier Sharing Setting.

---

### 6.2 Source File Expected Columns

The user provides `source_data/source_business_entities.xlsx`. The script must read (at minimum) these columns:

```
Name
Alternate Name              (optional — may not exist)
Type
Status
Formation Type
Line 1 (Street)
Line 2 (Street 2)           (optional)
Line 3 (Street 3)           (optional)
Line 4 (Street 4)           (optional)
City
State
Postal Code
Country Code
External Reference Name 1   (optional)
External Reference Value 1  (optional)
External Reference Name 2   (optional)
External Reference Value 2  (optional)
```

---

### 6.3 Row Generation Logic

For each data row in the source file (starting from row 2), generate a **contiguous block** of 3 to 5 rows in this exact sequence:

```
1. Business Entity row       (always)
2. Contact row               (always — placeholder, all fields blank except column A)
3. Address row               (always)
4. BE External Reference row (only if Ext Ref Name 1 OR Value 1 is non-empty)
5. BE External Reference row (only if Ext Ref Name 2 OR Value 2 is non-empty)
```

There must be **no blank rows** between blocks or within blocks.

---

### 6.4 Field Mappings

#### Business Entity row
| Target Column | Source Mapping |
|---|---|
| A — literal | `"Business Entity"` |
| B — ID | blank |
| C — Name | Source `Name` |
| D — Display Name | blank |
| E — Type | Source `Type` |
| F — Status | Source `Status` |
| G — Country of Origin Code | blank |
| H — State of Origin | blank |
| I — Formation Type | Source `Formation Type` |
| J — Business Entity Alternate Names | Source `Alternate Name` if non-empty, else blank |
| K — Parent Business Entity Id | blank |

#### Contact row
| Target Column | Value |
|---|---|
| A — literal | `"Contact"` |
| B through I | blank |

#### Address row
| Target Column | Source Mapping |
|---|---|
| A — literal | `"Address"` |
| B — Id | blank |
| C — Primary | blank |
| D — Name | blank |
| E — Line 1 | Source `Line 1 (Street)` |
| F — Line 2 | Source `Line 2 (Street 2)` |
| G — Line 3 | Source `Line 3 (Street 3)` |
| H — Line 4 | Source `Line 4 (Street 4)` |
| I — City | Source `City` |
| J — State | Source `State` |
| K — Postal Code | Source `Postal Code` |
| L — Country Code | Source `Country Code` |
| M — Plant | blank |

#### Business Entity External Reference row(s)
Generate **first** ext ref row if `External Reference Name 1` OR `External Reference Value 1` is non-empty:

| Target Column | Source Mapping |
|---|---|
| A — literal | `"Business Entity External Reference"` |
| B — ID | blank |
| C — Name | Source `External Reference Name 1` |
| D — Type | blank |
| E — Value | Source `External Reference Value 1` |

Generate **second** ext ref row if `External Reference Name 2` OR `External Reference Value 2` is non-empty:

| Target Column | Source Mapping |
|---|---|
| A — literal | `"Business Entity External Reference"` |
| B — ID | blank |
| C — Name | Source `External Reference Name 2` |
| D — Type | blank |
| E — Value | Source `External Reference Value 2` |

---

### 6.5 Critical Data Handling Rules

These must be enforced exactly — Coupa bulk upload is sensitive to formatting:

- **No scientific notation.** All values are written as plain text strings. Use `openpyxl` data type `str` for all cells — do not let Excel auto-convert numbers.
- **No rounding.** Values are written exactly as read from source.
- **No comma insertion.** Do not format numeric values with commas.
- **Do not trim leading zeros.** Postal codes, IDs, and codes must be written as-is.
- **Whitespace:** Strip leading/trailing whitespace from source values before writing. Do not strip internal whitespace.
- **Do not add columns.** Target file must have exactly the columns specified per header row — no extras.
- **Do not modify header text.** Header rows must match the spec character-for-character.

---

### 6.6 Script Implementation Notes for Claude Code

```python
"""
scripts/00_build_be_load_file.py

Generates the Coupa Business Entity Load File from source_business_entities.xlsx.
This is a PREREQUISITE step — run before the main pipeline.
Output: outputs/Target_Business_Entity_Load_File.xlsx

Usage: python scripts/00_build_be_load_file.py
"""

# Key implementation requirements:
# 1. Use openpyxl to write all cells. Write all values as str() to prevent
#    Excel auto-formatting (scientific notation, date conversion, etc.)
# 2. Apply ws.cell(row, col).data_type = 's' or prefix numeric-looking values
#    with a leading space if needed to force text treatment.
# 3. The safer approach: use number_format = '@' (text format) on all data columns.
# 4. After writing, validate row count:
#    expected = sum(3 + bool(ref1) + bool(ref2) for each source row) + 5 header rows
#    assert ws.max_row == expected, f"Row count mismatch: got {ws.max_row}"
# 5. Log: how many source rows processed, how many target rows written,
#    how many had Ext Ref 1, how many had Ext Ref 2.
# 6. Collect any missing required fields (Name, Type, Status) as WARNINGs in summary log.
```

---

## 7. Data Schemas (All Excel files)

### 7.1 extracted_fields.xlsx

| Column | Type | Description |
|---|---|---|
| ContractID | str | Unique ID assigned at intake (`CTR-001`) |
| FileName | str | Original filename |
| FieldName | str | Field extracted (see schema.json) |
| ExtractedValue | str | LLM-extracted value (empty string if unknown) |
| Confidence | float | 0.0–1.0 |
| EvidencePage | int | Page where evidence was found (null if unknown) |
| EvidenceSnippet | str | Short quote ≤100 chars from source |
| IsNull | bool | True if LLM returned null |
| NullReason | str | LLM explanation for null |
| ExtractionTimestamp | datetime | When extraction ran |

### 7.2 risk_signals.xlsx

| Column | Type | Description |
|---|---|---|
| ContractID | str | |
| RuleID | str | Rule that fired (e.g., `R001`) |
| SeverityTier | str | `High`, `Medium`, `Low` |
| Message | str | Plain-language callout |
| Evidence | str | Snippet or value that triggered rule |
| FieldTriggered | str | Which field caused the rule to fire |
| RuleTimestamp | datetime | |

### 7.3 summaries.xlsx

| Column | Type | Description |
|---|---|---|
| ContractID | str | |
| FileName | str | |
| Summary | str | 3–5 sentence plain-language summary |
| ContractType | str | Detected contract type |
| SummaryTimestamp | datetime | |

### 7.4 validation_review.xlsx (PRIMARY HUMAN REVIEW ARTIFACT)

| Column | Type | Description |
|---|---|---|
| ContractID | str | |
| FileName | str | |
| FieldName | str | |
| ExtractedValue | str | AI-extracted value |
| Confidence | float | |
| EvidencePage | int | |
| EvidenceSnippet | str | |
| SeverityFlag | str | Highest risk severity for this field (blank if none) |
| RiskMessage | str | Plain-language risk callout (blank if none) |
| ReviewerOverride | str | **[REVIEWER FILLS]** Corrected value |
| ChangeReason | str | **[REVIEWER FILLS]** Why they changed it |
| Approved | str | **[REVIEWER FILLS]** `YES` or `NO` |
| Reviewer | str | **[REVIEWER FILLS]** Name/initials |
| ReviewTimestamp | datetime | **[REVIEWER FILLS]** |
| FinalValue | str | Formula: `=IF(J2<>"",J2,D2)` — auto-resolves to override or extracted value |

Sheet tabs: `Review` (main), `Summaries`, `Risk Signals` (read-only copy)

### 7.5 coupa_ready.xlsx (Contract header data — post-approval)

Flat header format. Only rows where `Approved = "YES"` are included.

| Column | Description |
|---|---|
| contract_name | Supplier + ContractType + ContractID |
| supplier_name | From FinalValue of Supplier |
| contract_type | From FinalValue of ContractType |
| effective_date | ISO date |
| expiration_date | ISO date |
| contract_value | From FinalValue |
| business_entity | From FinalValue of BusinessEntity |
| governing_law | From FinalValue |
| auto_renewal | `Yes` / `No` / `Unknown` |
| payment_terms | From FinalValue |
| source_file | Original filename |
| extracted_by | `AI-POC-v1` |
| approved_by | From Reviewer column |
| approval_date | From ReviewTimestamp |
| coupa_upload_status | Always `PENDING` — never auto-changes |

### 7.6 rules.xlsx (Editable by business users)

| Column | Type | Description |
|---|---|---|
| RuleID | str | `R001`, `R002`, etc. |
| RuleType | str | `missing_field`, `date_check`, `clause_check`, `value_check` |
| Target | str | Field or clause name |
| Condition | str | `is_null`, `past_due`, `within_90_days`, `present`, `missing`, `below_threshold` |
| Severity | str | `High`, `Medium`, `Low` |
| MessageTemplate | str | Plain-language message |
| Enabled | str | `YES` or `NO` |

#### Seed rules

| RuleID | RuleType | Target | Condition | Severity | MessageTemplate | Enabled |
|---|---|---|---|---|---|---|
| R001 | missing_field | ExpirationDate | is_null | High | No expiration date found — contract may be open-ended | YES |
| R002 | missing_field | ContractValue | is_null | Medium | Contract value not extracted — manual review required | YES |
| R003 | missing_field | Supplier | is_null | High | Supplier name missing — contract cannot be staged for Coupa | YES |
| R004 | date_check | ExpirationDate | past_due | High | Contract appears expired — verify active status before use | YES |
| R005 | date_check | ExpirationDate | within_90_days | Medium | Contract expiring within 90 days — renewal decision needed | YES |
| R006 | clause_check | AutoRenewal | present | Medium | Auto-renewal clause detected — review opt-out window | YES |
| R007 | clause_check | LiabilityCap | missing | High | No liability cap clause found — legal review recommended | YES |
| R008 | missing_field | BusinessEntity | is_null | High | Business entity not identified — Coupa upload will be blocked | YES |
| R009 | missing_field | GoverningLaw | is_null | Low | Governing law not found — flag for legal awareness | YES |
| R010 | value_check | Confidence | below_threshold | Medium | Low confidence extraction — evidence should be manually verified | YES |

---

## 8. Field Extraction Schema (schema.json)

```json
{
  "schema_version": "1.0",
  "fields": [
    { "name": "Supplier", "description": "Primary supplier or vendor party name", "type": "string", "required": true },
    { "name": "ContractType", "description": "Type of contract (e.g., Master Service Agreement, NDA, Statement of Work, Purchase Agreement)", "type": "string", "required": true },
    { "name": "EffectiveDate", "description": "Contract start or effective date in ISO 8601 format (YYYY-MM-DD)", "type": "date", "required": true },
    { "name": "ExpirationDate", "description": "Contract end or expiration date in ISO 8601 format (YYYY-MM-DD)", "type": "date", "required": true },
    { "name": "ContractValue", "description": "Total contract value or maximum commitment amount", "type": "string", "required": false },
    { "name": "BusinessEntity", "description": "Internal company entity or business unit this contract is associated with", "type": "string", "required": true },
    { "name": "GoverningLaw", "description": "State or jurisdiction governing this contract", "type": "string", "required": false },
    { "name": "PaymentTerms", "description": "Payment terms (e.g., Net 30, Net 60, upon delivery)", "type": "string", "required": false },
    { "name": "AutoRenewal", "description": "Whether the contract contains an auto-renewal clause. Return PRESENT or NOT_FOUND.", "type": "string", "required": false },
    { "name": "LiabilityCap", "description": "Whether the contract contains a liability cap clause. Return PRESENT or NOT_FOUND.", "type": "string", "required": false },
    { "name": "TerminationClause", "description": "Whether the contract contains a termination for convenience clause. Return PRESENT or NOT_FOUND.", "type": "string", "required": false }
  ]
}
```

---

## 9. Script Specifications

### Script 01 — generate_mocks.py

Only run if real sample contracts are unavailable. Generates 15 mock contracts.

| # | Type | Format | Scenario |
|---|---|---|---|
| 1–4 | MSA | PDF (text) | Clean, all fields present |
| 5–7 | SOW | PDF (text) | Clean, some missing fields (LiabilityCap missing in 2 of 3) |
| 8–9 | NDA | DOCX | Clean, short |
| 10–11 | Purchase Agreement | PDF (text) | Expiring within 90 days → fires R005 |
| 12 | Service Agreement | PDF (text) | Already expired → fires R004 |
| 13 | MSA | PDF (text) | Auto-renewal clause present → fires R006 |
| 14 | SOW | DOCX | Missing ExpirationDate intentionally → fires R001 |
| 15 | Agreement | PDF (image) | Messy, degraded scan → OCR fallback |

All mock contracts must include footer: `[SIMULATED DATA — FOR POC DEMONSTRATION ONLY — NOT A REAL CONTRACT]`

---

### Script 02 — intake.py

**Purpose:** Scan the flat `contracts/` folder (and `mock_contracts/` if populated), assign ContractIDs, create catalog.

**Key change from v2:** Single folder walk — no subdirectory routing needed.

**Output:** `outputs/contract_catalog.xlsx`  
**Columns:** ContractID, FileName, FilePath, FileType, IntakeTimestamp

---

### Script 03 — extract_text.py

**Purpose:** Extract raw text + page maps from every cataloged contract.

**OCR routing logic:**
```python
def extract_text(file_path: Path) -> tuple[str, dict]:
    suffix = file_path.suffix.lower()
    if suffix == ".docx":
        return extract_docx(file_path)
    elif suffix == ".pdf":
        text, page_map = extract_pdf_text(file_path)       # try pdfplumber first
        if len(text.strip()) < OCR_MIN_TEXT_LENGTH:
            logger.warning(f"Low text yield on {file_path.name} — falling back to OCR")
            text, page_map = extract_pdf_ocr(file_path)    # pytesseract fallback
        return text, page_map
```

**Error handling:** If extraction fails entirely, write `EXTRACTION_FAILED` to the `.txt` file and log `ERROR` to summary. Continue to next contract — do not halt pipeline.

**Outputs:**
- `outputs/contract_text/{ContractID}.txt`
- `outputs/page_maps/{ContractID}.json` — `{"1": "page 1 text...", "2": "page 2 text..."}`

---

### Script 04 — extract_fields.py

**LiteLLM call pattern:**

```python
SYSTEM_PROMPT = """
You are a contract data extraction assistant.
Rules:
1. Only extract values explicitly stated in the contract text. Do not infer or fabricate.
2. If a field cannot be found, return null for value and explain in null_reason.
3. For each extracted value, identify the page number and a short quote (under 100 characters).
4. Confidence 0.0–1.0. Be conservative — only use 0.9+ for values clearly and explicitly stated.
5. Return ONLY valid JSON. No markdown, no preamble, no explanation outside the JSON.

Output format — JSON array, one object per field:
[
  {
    "field_name": "Supplier",
    "extracted_value": "Apex Industrial Services",
    "confidence": 0.95,
    "evidence_page": 1,
    "evidence_snippet": "entered into by Apex Industrial Services (Supplier)",
    "is_null": false,
    "null_reason": null
  }
]
"""
```

**Page-marked input format:**
```
--- PAGE 1 ---
[page 1 text]
--- PAGE 2 ---
[page 2 text]
```

**Token limit:** Truncate to first 8,000 words if needed. Log a WARNING with the ContractID when truncation occurs.

**Retry logic:** Invalid JSON → one retry with repair prompt. Second failure → mark all fields `EXTRACTION_FAILED` for that contract and log ERROR.

---

### Script 05 — run_rules.py

Evaluate extracted fields against `rules.xlsx`. Only evaluates rules where `Enabled == "YES"`.

**Rule evaluation logic:**
```python
def evaluate_rule(rule, field_value, confidence, contract_id):
    rt = rule["RuleType"]
    cond = rule["Condition"]

    if rt == "missing_field" and cond == "is_null":
        if not field_value or str(field_value).strip() == "":
            return build_signal(rule, contract_id, field_value)

    elif rt == "date_check":
        parsed = safe_parse_date(field_value)
        if parsed:
            if cond == "past_due" and parsed < date.today():
                return build_signal(rule, contract_id, field_value)
            if cond == "within_90_days":
                days = (parsed - date.today()).days
                if 0 <= days <= 90:
                    return build_signal(rule, contract_id, field_value)

    elif rt == "clause_check":
        if cond == "present" and field_value == "PRESENT":
            return build_signal(rule, contract_id, field_value)
        if cond == "missing" and field_value in (None, "", "NOT_FOUND"):
            return build_signal(rule, contract_id, field_value)

    elif rt == "value_check" and cond == "below_threshold":
        if float(confidence or 0) < CONFIDENCE_THRESHOLD_WARN:
            return build_signal(rule, contract_id, field_value)

    return None
```

---

### Script 06 — summarize.py

**LiteLLM summary prompt:**

```python
SYSTEM_PROMPT = """
You are a contract review assistant helping category managers quickly understand contracts.
Write a 3-5 sentence plain-language summary. Focus on: parties, what the contract covers,
key dates, value, and notable terms. Write for a business reader, not a lawyer.
Do not fabricate details. If something is unclear, say so.
Return only the summary text — no headers, bullets, or JSON.
"""
```

---

### Script 07 — build_validation.py

Assembles `validation_review.xlsx` from all prior outputs.

**Steps:**
1. Start with every row in `extracted_fields.xlsx`
2. Left join `risk_signals.xlsx` on ContractID + FieldTriggered — take highest severity per field where multiple rules fire
3. Add blank reviewer columns: `ReviewerOverride`, `ChangeReason`, `Approved`, `Reviewer`, `ReviewTimestamp`
4. Insert FinalValue formula: `=IF(J2<>"",J2,D2)`
5. Apply conditional formatting:
   - Red fill: SeverityFlag = `"High"`
   - Yellow fill: SeverityFlag = `"Medium"` OR Confidence < 0.6
   - Green fill: Approved = `"YES"`
6. Add dropdown data validation on `Approved` column: `YES, NO`
7. Freeze top row, auto-fit columns
8. Add `Summaries` sheet (from summaries.xlsx) and `Risk Signals` sheet (read-only copy)

---

### Script 08 — coupa_artifact.py

Generates `coupa_ready.xlsx` from approved rows only.

**Steps:**
1. Read `validation_review.xlsx`, filter `Approved == "YES"`
2. Pivot long → wide (one row per contract using FinalValue)
3. Map to Coupa column names (section 7.5)
4. Set `coupa_upload_status = "PENDING"` on all rows
5. Add red warning banner: `Generated: {timestamp} | By: AI-POC-v1 | Status: PENDING — HUMAN REVIEW REQUIRED BEFORE UPLOAD`

---

### run_pipeline.py (Master Orchestrator)

```python
"""
Usage:
  python run_pipeline.py           # Run all steps (02–07)
  python run_pipeline.py --step 3  # Run only step 3
  python run_pipeline.py --from 4  # Run steps 4 onwards
  python run_pipeline.py --be      # Run step 00 (BE load file) only

Note: Step 00 (BE load file) is NOT part of the default run.
      Run separately: python run_pipeline.py --be
"""
```

Each step prints: `[STEP N] Starting — {description}` and `[STEP N] ✓ Complete — {n} records → {output_file}`

Pipeline halts on ERROR and prints the failed step + path to log file for diagnosis.

---

## 10. Power BI Setup

### Data connections
Power BI connects directly to Excel files in `outputs/`. Use **Get Data → Excel Workbook**.

**Tables to import:**
- `extracted_fields.xlsx` → `ExtractedFields`
- `risk_signals.xlsx` → `RiskSignals`
- `summaries.xlsx` → `Summaries`
- `validation_review.xlsx` (Review sheet) → `ValidationReview`
- `coupa_ready.xlsx` → `CoupaPayload`

**Relationships:**
- `ExtractedFields[ContractID]` → `RiskSignals[ContractID]`
- `ExtractedFields[ContractID]` → `Summaries[ContractID]`
- `ValidationReview[ContractID]` → `Summaries[ContractID]`

### Page 1 — Portfolio View
KPI cards: Total Contracts | High Risk Count | Pending Review | Approved for Coupa  
Stacked bar: Contracts by Risk Tier  
Table: All contracts with Supplier, ContractType, ExpirationDate, Risk Tier, Review Status, Summary  
Slicer: ContractType, SeverityTier, Review Status  
Subtitle: `"Simulated Data — POC Demonstration Only"`

### Page 2 — Contract Detail View
Slicer: Select ContractID  
Card panel: Supplier | ContractType | Effective Date | Expiration Date | Value  
Text box: Summary  
Table: All extracted fields — FieldName, FinalValue, Confidence, EvidencePage, SeverityFlag, RiskMessage  
Conditional formatting: Color rows by SeverityFlag

### Page 3 — Review Quality View
KPI cards: Total Fields | Fields Corrected | Correction Rate % | Avg Confidence  
Bar chart: Fields Corrected by Contract  
Table: All corrections — FieldName, ExtractedValue, ReviewerOverride, ChangeReason, Reviewer  
Donut: Approved vs Pending vs Rejected

---

## 11. Demo Script (Thursday Walkthrough — ~7 minutes)

### Beat 1 — Today's Pain (60s)
Manual uploads, quality issues found after ingestion, legal bottleneck, 24-hour analytics delay. Open Power BI → Portfolio View.

### Beat 2 — Bulk Ingestion + Extraction (90s)
Show terminal briefly: `python run_pipeline.py`. Point to 15 contracts visible in Portfolio View with 11 fields each.

### Beat 3 — Explainable Risk Signals (90s)
Click High-risk contract → Detail View → show red rows. Point to specific rules firing (R001, R006). Open `rules.xlsx` briefly — "business users can add rules without touching code."

### Beat 4 — Human Correction (90s)
Open `validation_review.xlsx`. Navigate to pre-planted error on CTR-009 (ExpirationDate). Correct it → add reason → type YES in Approved. Back to Power BI → Refresh → Review Quality page shows correction logged.

### Beat 5 — Gated Coupa Artifacts (60s)
Open `coupa_ready.xlsx` — show red warning banner, only approved contracts present.  
Then show `Target_Business_Entity_Load_File.xlsx` briefly — "Before contracts can go to Coupa, business entities must be validated. This file handles that prerequisite step."

### Beat 6 — Scalability Signal (30s)
"Same pipeline handles 150 or 1,500 contracts. Next steps: GCP storage, scheduled refresh, live Coupa API."

---

## 12. Thursday Timeline

| Day | Phase | Target |
|---|---|---|
| **Mon Apr 20** | Session 1: Scaffold + git + mocks | Folder structure, .gitignore, requirements, config, schema, PROGRESS.md, 15 mock contracts |
| **Tue Apr 21** | Sessions 2–3: Intake + OCR + LLM extraction | extracted_fields.xlsx populated and spot-checked |
| **Wed Apr 22 AM** | Sessions 4–5: Rules + summaries + validation + Coupa artifacts | validation_review.xlsx complete and formatted, both Coupa files generating |
| **Wed Apr 22 PM** | Session 6: Power BI | All 3 pages built, data refreshing from Excel |
| **Thu Apr 24 AM** | Session 7: Cleanup + dry run | README, final PROGRESS.md, demo run x2, pre-plant CTR-009 error |

---

## 13. Claude Code Session Sequence

### Session 1 — Scaffold + Git + Mocks
```
cd C:\Users\jonesbrade\Documents\ai-contracts-poc
git init
claude.cmd /plan "Initialize the AI Contracts POC project: create directory structure, .gitignore, requirements.txt, config.py, schema.json, logger.py, initial PROGRESS.md header, and run 01_generate_mocks.py"
```
End of session: `git add . && git commit -m "Session 1: Scaffold + mock contracts"`

### Session 2 — Intake + Text Extraction
```
claude.cmd /plan "Write and run scripts 02_intake.py and 03_extract_text.py per the build guide. Use logger.py for all logging. Output contract_catalog.xlsx, contract_text files, and page_maps."
```
End of session: `git add . && git commit -m "Session 2: Intake + text extraction pipeline"`

### Session 3 — LLM Field Extraction
```
claude.cmd /plan "Write and run 04_extract_fields.py per the build guide. Use the LiteLLM local proxy (config from config.py). Output extracted_fields.xlsx. Log all warnings and errors via logger.py."
```
**Approval checkpoint:** Open extracted_fields.xlsx. Spot-check 3 contracts. Verify evidence snippets are real quotes, null_reasons are explanatory.

End of session: `git add . && git commit -m "Session 3: LLM field extraction"`

### Session 4 — Rules Engine + Summaries
```
claude.cmd /plan "Create rules.xlsx with seed rules from the build guide. Write and run 05_run_rules.py and 06_summarize.py. Output risk_signals.xlsx and summaries.xlsx."
```
**Approval checkpoint:** Verify at least 3 rules fire on expected contracts (R001 on CTR-014, R004 on CTR-012, R005 on CTR-010/011).

End of session: `git add . && git commit -m "Session 4: Rules engine + summaries"`

### Session 5 — Validation Table + Coupa Artifacts
```
claude.cmd /plan "Write and run 07_build_validation.py and 08_coupa_artifact.py per the build guide. Also write 00_build_be_load_file.py per the BE load file spec. Ensure validation_review.xlsx has conditional formatting, FinalValue formula, and YES/NO dropdown on Approved column."
```
**Approval checkpoint:** 
- Open validation_review.xlsx — does formatting work, does FinalValue formula resolve?
- Manually approve 3 contracts, run script 08 — does coupa_ready.xlsx generate with only those 3?
- If you have a sample `source_business_entities.xlsx`, test script 00 now.

End of session: `git add . && git commit -m "Session 5: Validation table + Coupa artifacts"`

### Session 6 — Orchestrator + Power BI
```
claude.cmd /plan "Write run_pipeline.py orchestrator with --step, --from, and --be flags per the build guide. Then provide step-by-step Power BI setup for the 3-page dashboard."
```
End of session: `git add . && git commit -m "Session 6: Orchestrator + Power BI setup"`

### Session 7 — Cleanup + README + Demo Prep
```
claude.cmd /plan "Write README.md with setup instructions, pipeline run guide, demo script outline, and known limitations. Update PROGRESS.md with final session entry. Run agentsys.cmd deslop on all Python scripts. Pre-plant the CTR-009 ExpirationDate error for the demo."
```
End of session: `git add . && git commit -m "Session 7: README + final cleanup — demo ready"`

---

## 14. Hallucination Controls (Non-Negotiable)

1. **Schema enforcement:** Invalid JSON → one retry → `EXTRACTION_FAILED` if still invalid
2. **No-fabricate instruction:** Explicit in system prompt. Unknowns return `null` + `null_reason`
3. **Provenance required:** Every non-null field must have `evidence_page` + `evidence_snippet`
4. **Rules-first risk:** Risk tier is computed by rules engine only — never by LLM judgment
5. **Human gate:** `coupa_ready.xlsx` only includes `Approved = "YES"` rows — enforced in code

---

## 15. Known Limitations (Disclose in Demo)

- OCR quality varies on scanned documents — Contract 15 is shown as an intentional hard case
- LLM accuracy is higher on structured contracts than non-standard agreements
- GCP storage is not yet integrated — IT approval in process
- Coupa writeback is demonstrated as staged artifacts only — live API is Phase 2
- Business entity validation gate is narrative-only in POC — blocking logic requires Coupa API credentials
- BE Load File requires a manually prepared source Excel — no automation of source data collection in POC

---

## Appendix A — Intentional Demo Error (Pre-Plant)

In `extracted_fields.xlsx`, manually change the `ExtractedValue` for `ContractID = CTR-009`, `FieldName = ExpirationDate` to the effective date (wrong value). Rebuild `validation_review.xlsx` — this row will appear highlighted yellow/red.

During Beat 4: show the wrong value → correct it in ReviewerOverride → add ChangeReason → set Approved = YES → refresh Power BI → Review Quality page shows the correction.

---

## Appendix B — Handoff Documentation Checklist (For IT/Team Onboarding)

When sharing beyond local machine:
- [ ] Document LiteLLM proxy URL + env var name (never the key itself)
- [ ] Document GCP project + bucket name once IT approves
- [ ] Document Tesseract install path and Windows installer URL
- [ ] Document Power BI workspace name + refresh instructions
- [ ] Verify `coupa_ready.xlsx` column mapping against live Coupa import template before Phase 2
- [ ] Verify `Target_Business_Entity_Load_File.xlsx` format against live Coupa BE upload template before use

---

*Build Guide Version 3 — Updated April 20, 2026*  
*Changes from v2: Added BE Load File script (00), simplified contracts/ to flat folder, added logging architecture (logger.py + summary Excel), added Git setup, added PROGRESS.md auto-update protocol*  
*Next version trigger: Post-demo leadership feedback + IT approval items*
