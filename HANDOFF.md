# AI Contracts POC — Project Handoff Document

**Owner:** Braden Jones (Tyson Foods)  
**As of:** April 21, 2026  
**Demo deadline:** Thursday, April 24, 2026 (EOD)  
**Builder pattern:** Braden owns architecture decisions; AI writes all code

---

## What This Project Is

A local Python pipeline that ingests contract documents (PDF and DOCX), extracts structured fields using an LLM, flags risk signals using a rules engine, generates plain-language summaries, and produces two Coupa-ready staging artifacts. All outputs are Excel files. The final deliverable is a working local prototype + Power BI dashboard demoed to Tyson Foods leadership.

---

## Hard Constraints (Non-Negotiable)

- **No GCP storage** — IT approval pending. All I/O is local Excel files.
- **No Coupa API writeback** — POC only. Coupa artifacts are staged Excel files for manual upload.
- **LLM via LiteLLM proxy only** — internal Tyson-hosted proxy at `https://litellm.tyson.com`. Model: `gemini/gemini-3-flash-preview`. All credentials via env vars, never hardcoded.
- **Single `main` branch** — one git commit per Claude Code session, no branching.
- **Python only for OCR** — `pdfplumber` (text PDFs) + `pytesseract` fallback (scanned/image PDFs). No cloud OCR.
- **Human gate is code-enforced** — `coupa_ready.xlsx` only contains rows where `Approved == "YES"` in `validation_review.xlsx`. This must never be relaxed.

---

## Current State

**Sessions complete:** 1 and 2 (of 7)  
**Next session:** Session 3 — LLM field extraction (`04_extract_fields.py`)

### What exists and has been verified

| Artifact | Status |
|---|---|
| Project directory structure | Complete |
| `.gitignore`, `requirements.txt`, `config.py`, `schema.json` | Complete |
| `scripts/logger.py` | Complete — shared module imported by all scripts |
| `scripts/01_generate_mocks.py` | Complete — 15 mock contracts in `mock_contracts/` |
| `scripts/02_intake.py` | Complete — run and verified |
| `scripts/03_extract_text.py` | Complete — run and verified |
| `outputs/contract_catalog.xlsx` | 15 rows, CTR-001 through CTR-015 |
| `outputs/contract_text/*.txt` | 15 files, all readable |
| `outputs/page_maps/*.json` | 15 files, page-level text |
| `CLAUDE.md` | Complete |

### What does NOT exist yet (Sessions 3–7)

- `scripts/00_build_be_load_file.py` — Coupa Business Entity Load File generator
- `scripts/04_extract_fields.py` — LLM field extraction **(Session 3 — next)**
- `scripts/05_run_rules.py` — Rules engine
- `scripts/06_summarize.py` — LLM plain-language summaries
- `scripts/07_build_validation.py` — Validation review Excel assembler
- `scripts/08_coupa_artifact.py` — Coupa-ready artifact generator
- `run_pipeline.py` — Master orchestrator
- `rules.xlsx` — Risk rules table (seed data defined in build guide)
- `outputs/extracted_fields.xlsx`, `risk_signals.xlsx`, `summaries.xlsx`, `validation_review.xlsx`, `coupa_ready.xlsx`
- Power BI dashboard (3 pages)
- `README.md`

---

## Pipeline Architecture

```
contracts/          →  02_intake.py          →  outputs/contract_catalog.xlsx
contract_catalog    →  03_extract_text.py    →  outputs/contract_text/*.txt
                                                outputs/page_maps/*.json
contract_text       →  04_extract_fields.py  →  outputs/extracted_fields.xlsx   (LiteLLM)
extracted_fields    →  05_run_rules.py       →  outputs/risk_signals.xlsx        (rules.xlsx)
contract_text       →  06_summarize.py       →  outputs/summaries.xlsx           (LiteLLM)
all outputs         →  07_build_validation.py→  outputs/validation_review.xlsx   (human review)
validation_review   →  08_coupa_artifact.py  →  outputs/coupa_ready.xlsx         (approved only)

Standalone prerequisite (run before pipeline):
source_data/        →  00_build_be_load_file.py → outputs/Target_Business_Entity_Load_File.xlsx
```

All scripts share `scripts/logger.py` for console + file + summary Excel logging. Input contracts are flat in `contracts/` (falls back to `mock_contracts/` when empty). ContractID (CTR-001 etc.) is the join key across all output files.

---

## LiteLLM Proxy Configuration

| Variable | Value |
|---|---|
| `LITELLM_API_BASE` | `https://litellm.tyson.com` |
| `LITELLM_API_KEY` | User's sk-key (set as Windows User env var) |
| `LITELLM_MODEL` | `gemini/gemini-3-flash-preview` |

**Important notes confirmed during setup:**
- This is a hosted proxy — do NOT attempt to run `litellm` CLI locally
- The `/health` endpoint returns 404 on this proxy — use `/models` to verify connectivity
- Verify with: `Invoke-WebRequest -Uri "$env:LITELLM_API_BASE/models" -Headers @{Authorization="Bearer $env:LITELLM_API_KEY"}`
- Proxy requires VPN connection to Tyson network
- `config.py` now includes `LITELLM_API_KEY = os.environ.get("LITELLM_API_KEY", "")`
- LiteLLM call pattern must pass `api_key=LITELLM_API_KEY` explicitly

---

## Mock Contracts (15 total — all in `mock_contracts/`)

Designed to exercise specific pipeline rules:

| ContractID | Type | Format | Scenario |
|---|---|---|---|
| CTR-001 to CTR-004 | MSA | PDF | Clean, all fields present |
| CTR-005 to CTR-007 | SOW | PDF | LiabilityCap missing in 2 of 3 |
| CTR-008 to CTR-009 | NDA | DOCX | Short, clean |
| CTR-010 to CTR-011 | Purchase Agreement | PDF | Expiring within 90 days → fires R005 |
| CTR-012 | Service Agreement | PDF | Already expired → fires R004 |
| CTR-013 | MSA | PDF | Auto-renewal clause → fires R006 |
| CTR-014 | SOW | DOCX | Missing ExpirationDate → fires R001 |
| CTR-015 | Agreement | PDF | Tagged as scanned/OCR — currently text PDF (poppler not installed) |

**CTR-009 is the demo error contract** — ExpirationDate will be pre-planted with a wrong value in Appendix A of the build guide for Beat 4 of the demo walkthrough.

---

## Key Data Schemas

### extracted_fields.xlsx (long format — one row per field per contract)
`ContractID | FileName | FieldName | ExtractedValue | Confidence | EvidencePage | EvidenceSnippet | IsNull | NullReason | ExtractionTimestamp`

### validation_review.xlsx (primary human review artifact)
Joins extracted fields + risk signals. Reviewer fills: `ReviewerOverride`, `ChangeReason`, `Approved` (YES/NO), `Reviewer`, `ReviewTimestamp`. `FinalValue` column uses formula `=IF(J2<>"",J2,D2)` to auto-resolve override vs extracted value.

### rules.xlsx (editable by business users — no code change needed)
10 seed rules covering: missing fields (R001–R003, R008–R009), date checks (R004–R005), clause checks (R006–R007), confidence threshold (R010).

---

## Remaining Session Plan

| Session | Target | Key Output |
|---|---|---|
| **Session 3** | `04_extract_fields.py` | `extracted_fields.xlsx` — spot-check 3 contracts before proceeding |
| **Session 4** | `rules.xlsx` seed data + `05_run_rules.py` + `06_summarize.py` | `risk_signals.xlsx`, `summaries.xlsx` — verify R001/R004/R005 fire on expected contracts |
| **Session 5** | `07_build_validation.py` + `08_coupa_artifact.py` + `00_build_be_load_file.py` | `validation_review.xlsx` with formatting + formulas, both Coupa files |
| **Session 6** | `run_pipeline.py` orchestrator + Power BI 3-page dashboard | Full end-to-end pipeline run |
| **Session 7** | `README.md`, cleanup, demo dry run, pre-plant CTR-009 error | Demo-ready state |

---

## Approval Checkpoints (Braden must review before proceeding)

1. **After Session 3:** Open `extracted_fields.xlsx` — spot-check 3 contracts. Verify evidence snippets are real quotes, null_reasons are explanatory.
2. **After Session 4:** Verify at least 3 rules fire on expected contracts (R001 on CTR-014, R004 on CTR-012, R005 on CTR-010/011).
3. **After Session 5:** Open `validation_review.xlsx` — verify conditional formatting, FinalValue formula, and YES/NO dropdown. Manually approve 3 rows, run script 08, verify only those 3 appear in `coupa_ready.xlsx`.
4. **After Session 5:** Verify `Target_Business_Entity_Load_File.xlsx` format matches Coupa spec (see build guide section 6).

---

## Open Issues

- Tesseract not installed — OCR fallback path untested. Not blocking for POC since CTR-015 is a text PDF.
- `LITELLM_API_KEY` must be set as a Windows User environment variable before Session 3 runs. Confirm with `echo $env:LITELLM_API_KEY` in a fresh PowerShell.
- `run_pipeline.py` orchestrator not yet written — scripts must be run individually until Session 6.

---

## Where to Find Everything

| Item | Location |
|---|---|
| Full build spec | `AI_Contracts_POC_Build_Guide_v3.md` |
| Session-by-session log | `PROGRESS.md` |
| Claude Code operating instructions | `CLAUDE.md` |
| All pipeline scripts | `scripts/` |
| All output artifacts | `outputs/` |
| Logs | `logs/pipeline_latest.log`, `logs/pipeline_log_summary.xlsx` |
| Mock contracts | `mock_contracts/` |
| User-provided source data | `source_data/` |
