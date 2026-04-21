# AI Contracts POC — Progress Log

**Project:** AI-assisted contract ingestion, extraction, and Coupa staging  
**Owner:** Braden Jones  
**Started:** April 20, 2026  
**Target:** April 24, 2026 (Thursday demo)  
**Guide version:** v3  

---

## Session 1 -- 2026-04-20 -- Scaffold + Mock Contracts

**What was built:**
- `.gitignore`, `requirements.txt`, `config.py`, `schema.json`, `PROGRESS.md`
- `scripts/logger.py` — shared logging module (console + timestamped file + summary Excel)
- `scripts/01_generate_mocks.py` — 15 mock contracts generated into `mock_contracts/`
- All project directories created

**Scripts added:**
- `logger.py`: Shared logging module imported by all pipeline scripts
- `01_generate_mocks.py`: Generates 15 mock PDFs and DOCX contracts covering all POC scenarios

**Key decisions made:**
- Working directory is `C:\Users\jonesbrade\ai-contracts-poc` (not Documents subfolder)
- logger.py LOGS_DIR set to `../logs` relative to scripts/ folder to match project root
- Unicode arrow characters removed from log messages for Windows cp1252 console compatibility

**Known issues / open items:**
- Tesseract not yet installed — required for CTR-015 (image PDF) OCR in Session 2
- CTR-015 generated as text PDF with a note; true image degradation requires poppler (pdf2image)
- `requirements.txt` packages not fully installed yet — install before Session 2: `pip install -r requirements.txt`

**Git commit:** `Session 1: Scaffold + mock contracts`

---

## Session 2 -- 2026-04-20 -- Intake + Text Extraction Pipeline

**What was built:**
- `CLAUDE.md` — session instructions for Claude Code in this repo
- `scripts/02_intake.py` — contract intake and catalog generation
- `scripts/03_extract_text.py` — text extraction + page map generation

**Scripts added:**
- `02_intake.py`: Scans `contracts/` (falls back to `mock_contracts/` if empty), assigns ContractIDs, writes `outputs/contract_catalog.xlsx`
- `03_extract_text.py`: Extracts text via pdfplumber (PDFs) or python-docx (DOCX) with pytesseract OCR fallback when text yield < 100 chars; outputs `contract_text/*.txt` and `page_maps/*.json`

**Key decisions made:**
- Intake preserves existing CTR-xxx IDs from mock contract filenames via regex — avoids re-assigning IDs to files that already carry them
- 03_extract_text.py uses a two-pass approach for PDFs: quick pdfplumber peek first, then OCR fallback if needed, rather than attempting OCR on every PDF
- CTR-015 extracted via pdfplumber (text PDF, not true image scan) — OCR fallback not triggered; expected per Session 1 notes

**Known issues / open items:**
- Tesseract still not installed — CTR-015 OCR fallback path is untested; install before demo or pre-verify
- True image-based PDF simulation requires poppler (pdf2image) — CTR-015 is text-based in current POC
- Session 3 next: write and run 04_extract_fields.py (LiteLLM field extraction)

**LiteLLM pre-work required before Session 3:**
- Proxy is hosted remotely (not localhost) — confirmed reachable and responding
- Correct models endpoint: `$env:LITELLM_API_BASE/models` (not `/health`, not `/v1/models`)
- Auth required: `Authorization: Bearer <key>` header on all requests
- To verify proxy before Session 3: `Invoke-WebRequest -Uri "$env:LITELLM_API_BASE/models" -Headers @{Authorization="Bearer $env:LITELLM_API_KEY"} | Select-Object -ExpandProperty Content`
- `config.py` needs `LITELLM_API_KEY` added — not present yet; Claude Code will add in Session 3
- Set env vars permanently so they survive PowerShell restarts:
  ```powershell
  [System.Environment]::SetEnvironmentVariable("LITELLM_API_BASE", "https://your-proxy-url", "User")
  [System.Environment]::SetEnvironmentVariable("LITELLM_API_KEY",  "your-sk-key",            "User")
  [System.Environment]::SetEnvironmentVariable("LITELLM_MODEL",    "model-name-from-list",   "User")
  ```
- Model name must be confirmed from the `/models` response before Session 3 begins

**Verified outputs:**
- `outputs/contract_catalog.xlsx`: 15 rows (CTR-001 through CTR-015)
- `outputs/contract_text/`: 15 .txt files, all readable
- `outputs/page_maps/`: 15 .json files with page-level text

**Git commit:** `Session 2: Intake + text extraction pipeline`

---

## Session 3 -- 2026-04-21 -- LLM Field Extraction

**What was built:**
- `scripts/04_extract_fields.py` — LiteLLM structured field extraction pipeline

**Scripts added:**
- `04_extract_fields.py`: Reads contract_catalog.xlsx + page_maps/*.json, calls LiteLLM hosted proxy for all 11 schema fields, writes outputs/extracted_fields.xlsx (165 rows, long format: one row per field per contract). Invalid JSON triggers one retry with repair prompt; second failure marks all fields EXTRACTION_FAILED. Low confidence and truncation events logged to WARNING.

**Key decisions made:**
- MAX_TOKENS_EXTRACTION raised from 2000 to 4096 — 2000 was insufficient for 11-field JSON responses; 3 contracts failed on first run, 0 on second run after the fix
- LiteLLM model: gemini/gemini-3-flash-preview via hosted proxy at LITELLM_API_BASE
- Low confidence (0.00) warnings on AutoRenewal/LiabilityCap/TerminationClause for contracts where the field returned null — model behavior; expected for NOT_FOUND clause checks
- strip_json_fences() added to handle markdown code fence wrapping from some model responses

**Spot-check results (approval checkpoint):**
- CTR-001: All 11 fields extracted, evidence snippets are real quotes from contract text, confidence 0.95 across all found fields
- CTR-013 AutoRenewal: "Successive one-year terms" (confidence 0.98) — auto-renewal clause correctly detected (expected: R006 fires in Session 4)
- CTR-014 ExpirationDate: "TBD" extracted — missing expiration scenario intact (expected: R001 fires in Session 4)
- 15/15 contracts succeeded, 0 failures

**Known issues / open items:**
- CTR-014 ExpirationDate returns "TBD" instead of null — rules engine in Session 4 should handle "TBD" as non-date gracefully
- Low confidence (0.00) on null/NOT_FOUND fields is a model behavior, not a code issue — rule R010 will correctly flag these in Session 4

**Git commit:** `Session 3: LLM field extraction`

---

## Session 4 -- 2026-04-21 -- Rules Engine + Summaries

**What was built:**
- `rules.xlsx` — seed rules table (10 rules, editable by business users)
- `scripts/05_run_rules.py` — data-driven rules engine
- `scripts/06_summarize.py` — LiteLLM plain-language summarizer

**Scripts added:**
- `05_run_rules.py`: Loads enabled rules from rules.xlsx, evaluates extracted fields for all 15 contracts, writes outputs/risk_signals.xlsx. 21 signals generated across 7 rule types.
- `06_summarize.py`: Calls LiteLLM for each contract, generates 3-5 sentence business-reader summary, writes outputs/summaries.xlsx. 15/15 contracts succeeded with retry logic handling transient None responses.

**Key decisions made:**
- clause_check "present" logic broadened: fires if value is non-empty and not "NOT_FOUND" (not just exact "PRESENT" match). Required because LLM returns descriptive text (e.g., "Successive one-year terms") instead of the canonical "PRESENT" token — which still means the clause is present.
- Retry logic added to 06_summarize.py: one retry with 2s delay on None LLM response (transient model behavior observed on 2-3 contracts per run).

**Approval checkpoint results:**
- R001 fired on CTR-014 (ExpirationDate = "TBD") -- YES
- R004 fired on CTR-012 (ExpirationDate = 2024-12-31, past due) -- YES
- R005 fired on CTR-010 (2026-05-15) and CTR-011 (2026-06-01) -- YES
- R006 fired on CTR-013 (AutoRenewal = "Successive one-year terms") -- YES (after clause_check fix)
- R007 fired on 6 contracts missing LiabilityCap
- All 21 signals correctly attributed

**Full signal breakdown:**
R001: 1 | R002: 2 | R003: 2 | R004: 6 | R005: 3 | R006: 1 | R007: 6

**Known issues / open items:**
- LLM occasionally returns None content on first attempt (transient) — retry handles it
- CTR-014 ExpirationDate = "TBD" (not null) — is_null_value() treats "TBD" as null; R001 fires correctly
- Session 5 next: 07_build_validation.py + 08_coupa_artifact.py + 00_build_be_load_file.py

**Git commit:** `Session 4: Rules engine + summaries`

---
