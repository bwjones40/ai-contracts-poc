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
