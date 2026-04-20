# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

AI Contracts POC — local Python pipeline for contract ingestion, LLM field extraction, rules-based risk flagging, and Coupa staging. Demo deadline: Thursday April 24, 2026. Owner: Braden Jones. All code is written by Claude Code; Braden owns architecture decisions.

**LLM:** LiteLLM **hosted proxy** (not localhost) — URL, API key, and model name all read from env vars, no hardcoded values.  
**Storage:** Excel files only (no GCP for POC).  
**OCR:** `pdfplumber` (text PDFs) + `pytesseract` fallback (scanned/image PDFs).

---

## Running the Pipeline

```bash
# Install dependencies (required before first run)
pip install -r requirements.txt

# Full pipeline (scripts 02–07)
python run_pipeline.py

# Single step
python run_pipeline.py --step 3

# From a specific step forward
python run_pipeline.py --from 4

# Business Entity Load File only (prerequisite step — run before main pipeline)
python run_pipeline.py --be
# or directly:
python scripts/00_build_be_load_file.py

# Generate mock contracts (if no real samples)
python scripts/01_generate_mocks.py
```

**Logs:** `logs/pipeline_latest.log` (most recent run) and `logs/pipeline_log_summary.xlsx` (WARNING/ERROR accumulation across all runs).

---

## Architecture

### Pipeline Flow (sequential scripts 02–07)

```
contracts/          →  02_intake.py         →  outputs/contract_catalog.xlsx
contract_catalog    →  03_extract_text.py   →  outputs/contract_text/*.txt + page_maps/*.json
contract_text       →  04_extract_fields.py →  outputs/extracted_fields.xlsx  (LiteLLM)
extracted_fields    →  05_run_rules.py      →  outputs/risk_signals.xlsx       (rules.xlsx engine)
contract_text       →  06_summarize.py      →  outputs/summaries.xlsx          (LiteLLM)
all outputs         →  07_build_validation.py → outputs/validation_review.xlsx (human review)
validation_review   →  08_coupa_artifact.py →  outputs/coupa_ready.xlsx        (approved rows only)
```

Script 00 (`00_build_be_load_file.py`) is a standalone prerequisite — not part of the default pipeline run. It transforms `source_data/source_business_entities.xlsx` into the Coupa-format `outputs/Target_Business_Entity_Load_File.xlsx`.

### Key Design Decisions

- **Flat input folder:** All contracts (PDF and DOCX) go into `contracts/` — no subfolders. `02_intake.py` also pulls from `mock_contracts/` if populated.
- **ContractID assignment:** Assigned at intake as `CTR-001`, `CTR-002`, etc. — this ID is the join key across all output Excel files.
- **Long-format extraction:** `extracted_fields.xlsx` is long (one row per field per contract), not wide. `08_coupa_artifact.py` pivots to wide for Coupa output.
- **Human gate is code-enforced:** `coupa_ready.xlsx` only includes rows where `Approved == "YES"` in `validation_review.xlsx`. This is enforced in `08_coupa_artifact.py`, not by convention.
- **Rules engine is data-driven:** Risk rules live in `rules.xlsx` (editable by business users, no code change needed). Only rules with `Enabled == "YES"` are evaluated.
- **LLM hallucination controls:** Invalid JSON → one retry → `EXTRACTION_FAILED` if still invalid. Every non-null field requires `evidence_page` + `evidence_snippet`. Risk tiers are computed by the rules engine only — never by LLM judgment.
- **OCR fallback threshold:** `OCR_MIN_TEXT_LENGTH = 100` chars. If `pdfplumber` yields less than this, `pytesseract` is invoked automatically.

### Logging Pattern (mandatory for all scripts)

Every script imports from `scripts/logger.py`. The pattern:

```python
from logger import get_logger, write_summary_xlsx
logger = get_logger(__name__)

# Collect WARNING/ERROR events throughout script execution
summary_events = []
# ... on warning: summary_events.append({"script": "04_extract_fields", "contract_id": cid, "level": "WARNING", "message": "..."})

# At script exit:
write_summary_xlsx(summary_events)
```

Log `INFO` at start/end of each major step: `[STEP N] Starting...` / `[STEP N] Complete — {n} records`. Log `WARNING` for recoverable issues (OCR fallback, low confidence). Log `ERROR` for failures but continue to next contract — never halt the pipeline on a single contract failure.

### LiteLLM Call Pattern

All LLM calls go through the hosted LiteLLM proxy. `config.py` needs `LITELLM_API_KEY` added (not present yet — add in Session 3). Call pattern:

```python
import litellm
response = litellm.completion(
    model=LITELLM_MODEL,
    messages=[...],
    api_base=LITELLM_API_BASE,
    api_key=LITELLM_API_KEY,
    max_tokens=MAX_TOKENS_EXTRACTION,
)
```

System prompts enforce: no fabrication, return null + null_reason for unknowns, return ONLY valid JSON, confidence 0.0–1.0.

### Coupa BE Load File Format (Script 00)

The output workbook has 5 header rows (Business Entity, Contact, Address, BE External Reference, Supplier Sharing Setting) followed by contiguous data blocks — no blank rows. **All cell values must be written as plain text strings** (use `number_format = '@'`) to prevent Excel auto-formatting postal codes and IDs. See build guide section 6 for the exact field mapping and row generation logic.

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `LITELLM_MODEL` | `gpt-4o` | Exact model name as returned by proxy `/models` endpoint |
| `LITELLM_API_BASE` | `http://localhost:4000` | Hosted proxy URL — must be set, default is wrong |
| `LITELLM_API_KEY` | *(none)* | Bearer key for the hosted proxy — **not in config.py yet, add in Session 3** |
| `TESSERACT_PATH` | `C:\Program Files\Tesseract-OCR\tesseract.exe` | Tesseract binary path |

**LiteLLM proxy notes (confirmed 2026-04-20):**
- Proxy is hosted remotely, not on localhost — do not attempt to start `litellm` CLI
- Health check: `/health` returns 404 on this proxy — use `/models` instead
- Auth: all requests require `Authorization: Bearer $env:LITELLM_API_KEY` header
- Verify before running Session 3: `Invoke-WebRequest -Uri "$env:LITELLM_API_BASE/models" -Headers @{Authorization="Bearer $env:LITELLM_API_KEY"} | Select-Object -ExpandProperty Content`
- Model name must match exactly what the `/models` response returns

Set all three permanently in PowerShell (once, then they persist):
```powershell
[System.Environment]::SetEnvironmentVariable("LITELLM_API_BASE", "https://your-proxy-url", "User")
[System.Environment]::SetEnvironmentVariable("LITELLM_API_KEY",  "your-sk-key",            "User")
[System.Environment]::SetEnvironmentVariable("LITELLM_MODEL",    "model-name-from-list",   "User")
```

Tesseract must be installed separately on Windows before OCR fallback works. Installer: https://github.com/UB-Mannheim/tesseract/wiki

---

## Git Convention

One commit per Claude Code session:
```
Session 1: Scaffold + mock contracts
Session 2: Intake + text extraction pipeline
Session 3: LLM field extraction
Session 4: Rules engine + summaries
Session 5: Validation table + Coupa artifacts
Session 6: Master orchestrator + Power BI setup
Session 7: Cleanup + README + final PROGRESS.md
```

`outputs/contract_text/`, `outputs/page_maps/`, `mock_contracts/`, and `logs/*.log` are gitignored (regenerated). Excel output files in `outputs/*.xlsx`, `rules.xlsx`, and `source_data/*.xlsx` ARE committed — they are demo artifacts.

---

## Session End Protocol

After every session, append to `PROGRESS.md` using the template in build guide section 4. Then commit:

```bash
git add .
git commit -m "Session [N]: [brief description]"
```

---

## Current Build State

Sessions 1 and 2 complete. Session 3 target: write and run `04_extract_fields.py` (LiteLLM field extraction).

**Approval checkpoints before proceeding:**
- After first extraction run (Session 3): spot-check extracted_fields.xlsx for evidence quality
- After validation Excel (Session 5): verify conditional formatting and FinalValue formula
- After BE Load File generation (Session 5): verify format matches Coupa spec
