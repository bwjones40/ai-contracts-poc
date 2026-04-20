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
