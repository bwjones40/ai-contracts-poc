# AUDIT_HANDOFF.md — AI Contracts POC

**Generated:** 2026-04-21  
**Author:** Claude Code audit pass  
**Source files:** `PROGRESS.md` (Sessions 1–4), `CLAUDE.md`, `config.py`, `scripts/05_run_rules.py`, `scripts/06_summarize.py`, `outputs/risk_signals.xlsx`, `outputs/summaries.xlsx` (all verified live)  
**Supersedes:** Previous `AUDIT_HANDOFF.md` (post-Session 3) and stale `HANDOFF.md` (Sessions 1–2 only)

---

## 1. Executive Summary

- **Session 4 is complete as of 2026-04-21.** `rules.xlsx` created, `05_run_rules.py` and `06_summarize.py` written, run, and committed (commit `38bc82a`). `risk_signals.xlsx` contains 21 signals, `summaries.xlsx` contains 15/15 rows — all verified.
- **All key approval checkpoint rules fired correctly:** R001 on CTR-014 (TBD expiration), R004 on CTR-012 (expired), R005 on CTR-010/011 (within 90 days), R006 on CTR-013 (auto-renewal clause), R007 on 6 contracts missing LiabilityCap.
- **One rules engine bug was found and fixed in-session:** R006 (`clause_check` / `present`) was not firing because the LLM returned "Successive one-year terms" instead of the canonical "PRESENT" token. Fix: broadened the `present` check to fire if value is non-empty and not "NOT_FOUND" — more robust to descriptive LLM output.
- **CTR-014 "TBD" date risk (flagged in Session 3 audit) is resolved.** `safe_parse_date()` treats "TBD" as unparseable → returns `None` → `is_null_value("TBD")` returns `True` → R001 fires correctly.
- **Summarize script had transient None responses from the LLM** (2–3 contracts per run). Added one-retry-with-delay pattern — 15/15 succeeded on final run.
- **Three sessions remain before Thursday demo (Sessions 5, 6, 7).** Session 5 is the heaviest: `07_build_validation.py`, `08_coupa_artifact.py`, `00_build_be_load_file.py` — all in one session. Timeline is tight but achievable.
- **No GCP, no Coupa API, no Tesseract** — all constraints hold. Not blocking.
- **Demo deadline is Thursday April 24, 2026 (EOD).** Today is April 21.

---

## 2. Product Vision and Telos

### What we are building

A local Python pipeline that:
1. Ingests contract documents (PDF and DOCX) from a flat input folder
2. Extracts structured fields (11 fields: Supplier, ContractType, dates, value, governing law, etc.) using an LLM
3. Runs a rules engine against extracted fields to flag risk signals (expired dates, missing liability caps, auto-renewal clauses, etc.)
4. Generates plain-language summaries of each contract
5. Assembles a human-review Excel (`validation_review.xlsx`) with conditional formatting, reviewer override columns, and a FinalValue formula
6. Produces two Coupa-staging artifacts: `coupa_ready.xlsx` (approved contracts only) and `Target_Business_Entity_Load_File.xlsx` (business entity prerequisite)
7. Visualizes the full portfolio in a Power BI dashboard (3 pages)

### Why it matters

Tyson Foods procurement is ingesting contracts into Coupa with manual data entry, creating: data quality risk before upload, no systematic risk flagging, 24-hour analytics delay, and legal review bottleneck. This POC demonstrates an AI-assisted alternative that is explainable (evidence snippets), auditable (rules-based risk engine), and gated (human approval before any Coupa artifact is generated).

### Desired end-state if fully successful

- Leadership approves Phase 2: GCP storage, scheduled pipeline refresh, live Coupa API writeback
- Pipeline handles 150–1,500 contracts with the same code, zero changes
- Category managers use `validation_review.xlsx` as their primary contract review surface
- Risk rules are maintained by business users directly in `rules.xlsx`, no IT involvement needed

---

## 3. Implementation Approach

### Architecture

Sequential Python scripts (02 → 03 → 04 → 05 → 06 → 07 → 08), each producing one Excel artifact consumed by the next. ContractID (`CTR-001` etc.) is the join key across all outputs. Script 00 is a standalone prerequisite for Coupa BE upload.

```
contracts/          →  02_intake.py         →  contract_catalog.xlsx         [DONE]
contract_catalog    →  03_extract_text.py   →  contract_text/*.txt + page_maps/*.json  [DONE]
page_maps           →  04_extract_fields.py →  extracted_fields.xlsx         [DONE]
extracted_fields    →  05_run_rules.py      →  risk_signals.xlsx             [DONE - Session 4]
contract_text       →  06_summarize.py      →  summaries.xlsx                [DONE - Session 4]
all outputs         →  07_build_validation  →  validation_review.xlsx        [Session 5]
validation_review   →  08_coupa_artifact    →  coupa_ready.xlsx              [Session 5]
source_data/        →  00_build_be_load_file→  Target_BE_Load_File.xlsx      [Session 5]
```

### Key technical decisions

| Decision | Rationale |
|---|---|
| Long-format `extracted_fields.xlsx` (one row per field per contract) | Enables per-field risk joins; `08_coupa_artifact.py` pivots wide for Coupa output |
| LLM extraction via LiteLLM proxy (not direct API) | All LLM calls must go through Tyson's internal proxy — IT constraint |
| Gemini `gemini/gemini-3-flash-preview` model | Fastest available on Tyson's proxy for POC turnaround |
| `strip_json_fences()` in extraction script | Gemini sometimes wraps JSON in ``` fences despite prompt instructions |
| `MAX_TOKENS_EXTRACTION = 4096` (raised from 2000) | 11-field JSON responses with evidence snippets exceed 2000 tokens |
| Rules engine is data-driven (rules.xlsx) | Business users can add/modify rules without touching code — key demo talking point |
| `clause_check` "present" fires on any non-empty, non-NOT_FOUND value | LLM returns descriptive text instead of "PRESENT" token — strict equality would miss real clauses |
| One retry with 2s delay in `06_summarize.py` on None LLM response | LLM intermittently returns None content — transient; retry recovers without user impact |
| Human gate is code-enforced, not convention | `coupa_ready.xlsx` only contains `Approved == "YES"` rows, enforced in `08_coupa_artifact.py` |
| No GCP, all Excel I/O | IT approval pending — hard constraint for POC phase |

### Why this approach over alternatives

- **No database:** IT approval for GCP not yet granted; Excel files are reviewable by non-technical stakeholders without tooling
- **No streaming/async:** Single-machine POC, sequential is simpler and debuggable
- **No Coupa API:** Live API requires credentials and approval not available before the demo
- **No Copilot Studio / cloud AI:** Keeps everything on the internal Tyson proxy, no data leaving the approved environment

---

## 4. Progress So Far

### Completed (Sessions 1–4)

| Script / Artifact | Status | Commit | Notes |
|---|---|---|---|
| Project directory structure | Done | `15a17a0` | |
| `.gitignore`, `requirements.txt` | Done | `15a17a0` | |
| `config.py` | Done + updated | multiple | `LITELLM_API_KEY` added S2; `MAX_TOKENS` bumped S3 |
| `schema.json` | Done | `15a17a0` | 11 fields defined |
| `scripts/logger.py` | Done | `15a17a0` | console + timestamped file + summary Excel |
| `scripts/01_generate_mocks.py` | Done, run | `15a17a0` | 15 mock contracts in `mock_contracts/` |
| `scripts/02_intake.py` | Done, run, verified | `b2f3402` | 15 rows in `contract_catalog.xlsx` |
| `scripts/03_extract_text.py` | Done, run, verified | `b2f3402` | 15 .txt + 15 .json page maps |
| `scripts/04_extract_fields.py` | Done, run, verified | `84a50c5` | 165 rows, 0 EXTRACTION_FAILED |
| `rules.xlsx` | Done | `38bc82a` | 10 seed rules (R001–R010), styled, editable |
| `scripts/05_run_rules.py` | Done, run, verified | `38bc82a` | 21 signals, all expected rules fired |
| `scripts/06_summarize.py` | Done, run, verified | `38bc82a` | 15/15 contracts summarized, retry logic included |
| `outputs/contract_catalog.xlsx` | Live | `b2f3402` | 15 contracts, CTR-001–CTR-015 |
| `outputs/extracted_fields.xlsx` | Live | `84a50c5` | 165 rows, 0 EXTRACTION_FAILED |
| `outputs/risk_signals.xlsx` | Live | `38bc82a` | 21 rows: R001×1, R002×2, R003×2, R004×6, R005×3, R006×1, R007×6 |
| `outputs/summaries.xlsx` | Live | `38bc82a` | 15 rows, all non-FAILED |
| `CLAUDE.md` | Done | `a0eb1fe` | Updated with LiteLLM proxy notes |

### In progress / next session (Session 5 — target Wed Apr 22)

- `scripts/07_build_validation.py` — assembles `validation_review.xlsx` with conditional formatting, FinalValue formula, YES/NO dropdown
- `scripts/08_coupa_artifact.py` — generates `coupa_ready.xlsx` from `Approved == "YES"` rows
- `scripts/00_build_be_load_file.py` — Coupa Business Entity Load File from `source_data/source_business_entities.xlsx`

**Approval checkpoint after Session 5:**
- Open `validation_review.xlsx` — formatting works, FinalValue formula resolves?
- Manually approve 3 contracts, run script 08 — only those 3 in `coupa_ready.xlsx`?
- If `source_data/source_business_entities.xlsx` is available, test script 00

### Not yet started (Sessions 6–7)

- `run_pipeline.py` — master orchestrator with `--step`, `--from`, `--be` flags
- Power BI dashboard (3 pages: Portfolio View, Contract Detail, Review Quality)
- `README.md`
- Pre-plant CTR-009 ExpirationDate demo error (Appendix A of build guide)
- Final `PROGRESS.md` update

---

## 5. Success Metrics

| Metric | Baseline | Current | Target | Measurement |
|---|---|---|---|---|
| Contracts processed end-to-end | 0 | 15 (through summaries) | 15 (full pipeline) | Row count in each output xlsx |
| LLM extraction success rate | — | 15/15 (100%) | 100% | Non-EXTRACTION_FAILED rows / total |
| Summarization success rate | — | 15/15 (100%) | 100% | Non-SUMMARY_FAILED rows / total |
| Rules firing on correct contracts | — | Verified: R001 CTR-014, R004 CTR-012, R005 CTR-010/011, R006 CTR-013, R007 on 6 contracts | All expected | Manual verify post-Session 4 — DONE |
| Total risk signals generated | — | 21 | ≥15 meaningful signals | `risk_signals.xlsx` row count |
| Human approval gate works | — | Not yet built | Only YES rows in coupa_ready.xlsx | Session 5 test: approve 3, verify only 3 appear |
| Demo runs without errors | — | Not yet tested | Clean end-to-end run in Session 7 | Full pipeline run + Power BI refresh |
| Evidence snippets are real quotes | — | Spot-checked CTR-001 ✓ | All non-null fields | Manual spot-check post-Session 3 (Braden) |

---

## 6. Hypotheses

### Main hypothesis

A sequential Python pipeline with LLM extraction + rules-based risk flagging + human review gate can process 15 mock contracts into Coupa-ready staging artifacts with sufficient accuracy and auditability to pass a Thursday leadership demo.

### Sub-hypotheses

| Hypothesis | Status | Confirmation signal | Notes |
|---|---|---|---|
| Gemini extracts contract fields accurately enough for a demo | **CONFIRMED** | 165 rows, 0 EXTRACTION_FAILED, real evidence quotes | Session 3 |
| Rules engine fires on correct scenario contracts | **CONFIRMED** | All 7 rule types fired on expected contracts | Session 4 — see risk register for R006 fix |
| CTR-014 "TBD" ExpirationDate triggers R001 | **CONFIRMED** | R001 signal present for CTR-014 in risk_signals.xlsx | Session 4 |
| `MAX_TOKENS_SUMMARY = 500` is sufficient | **CONFIRMED** | 15/15 summaries complete, none truncated | Session 4 |
| LLM clause_check returns canonical "PRESENT" token | **FALSIFIED** | CTR-013 AutoRenewal returned "Successive one-year terms" | Fixed by broadening clause_check logic |
| `validation_review.xlsx` conditional formatting works in Excel | **UNTESTED** | Session 5 will reveal | openpyxl formatting → Excel rendering risk |
| Human gate formula and formatting work in Excel | **UNTESTED** | FinalValue formula resolves correctly post-openpyxl write | Session 5 will reveal |
| `MAX_TOKENS_EXTRACTION = 4096` is sufficient | **CONFIRMED** | 15/15 on second run post-fix | Session 3 |

---

## 7. Evidence vs Assumptions

| Claim | Type | Source | Confidence | Notes |
|---|---|---|---|---|
| 15/15 contracts extracted with 0 EXTRACTION_FAILED | Evidence | `outputs/extracted_fields.xlsx` verified live 2026-04-21 | High | `ws.max_row - 1 = 165`; no EXTRACTION_FAILED values found |
| CTR-001 evidence snippets are real contract quotes | Evidence | Spot-check: `"Apex Industrial Services LLC ("Supplier")"` | High | Direct quote match to `page_maps/CTR-001.json` page 1 |
| CTR-013 AutoRenewal = "Successive one-year terms" (not "PRESENT") | Evidence | `extracted_fields.xlsx` row read 2026-04-21 | High | LLM returns descriptive text; rules engine now handles |
| CTR-014 ExpirationDate = "TBD" (not null) | Evidence | `extracted_fields.xlsx` row read 2026-04-21 | High | `is_null_value("TBD")` returns True; R001 fires correctly |
| R001 fires on CTR-014 | Evidence | `risk_signals.xlsx` row: CTR-014, R001, High | High | Verified 2026-04-21 |
| R004 fires on CTR-012 | Evidence | `risk_signals.xlsx` row: CTR-012, R004, High, 2024-12-31 | High | Verified 2026-04-21 |
| R005 fires on CTR-010 and CTR-011 | Evidence | `risk_signals.xlsx` rows: CTR-010 (2026-05-15), CTR-011 (2026-06-01) | High | Verified 2026-04-21 |
| R006 fires on CTR-013 (auto-renewal) | Evidence | `risk_signals.xlsx` row: CTR-013, R006, Medium | High | Required clause_check fix in Session 4 |
| R007 fires on 6 contracts (no LiabilityCap) | Evidence | `risk_signals.xlsx` R007×6 | High | CTR-005, CTR-006, CTR-008, CTR-009, CTR-014, CTR-015 |
| 15/15 summaries generated without SUMMARY_FAILED | Evidence | `outputs/summaries.xlsx` verified live 2026-04-21 | High | Retry logic handled transient None responses |
| LLM intermittently returns None content | Evidence | 3 transient failures across 2 full runs (CTR-001, CTR-006, CTR-008) | High | Transient — retry recovers every time |
| Gemini returns confidence 0.0 for null/NOT_FOUND fields | Evidence | 29 WARNING events in pipeline log | High | Expected model behavior |
| R010 (low confidence) NOT present in risk_signals.xlsx | Evidence | Signal breakdown: no R010 rows | High | R010 only fires if field has a value AND confidence < 0.6; low-conf fields are null — correct |
| openpyxl conditional formatting renders in Excel | Assumption | Standard openpyxl feature; not tested in this session | Med | Session 5 must open file in Excel and verify |
| FinalValue `=IF(J2<>"",J2,D2)` formula survives openpyxl write | Assumption | openpyxl can write formula strings; depends on Excel version reading | Med | Session 5 test |
| Power BI can connect to local Excel outputs | Assumption | Standard Power BI feature; file paths stable | Med | Session 6 test |
| Demo can run end-to-end without errors by Thursday | Assumption | 3 sessions remaining, 3 days — achievable | Med | Risk: Session 5 runs long |
| Tesseract is not needed for this POC | Evidence | CTR-015 is text PDF; pdfplumber extracted it successfully | High | OCR fallback path fully untested — not a demo risk |
| LiteLLM proxy requires VPN | Evidence | Hosted at Tyson internal URL | High | Must be on VPN during Sessions 5–7 |

---

## 8. Failure Modes and Risk Register

Ranked by impact × likelihood:

| Risk | Impact | Likelihood | Detection | Mitigation |
|---|---|---|---|---|
| Session 5 runs long — insufficient time for demo prep | High — demo fails | Med — Scripts 07, 08, and 00 are all complex | Track wall-clock time; check against plan | Pre-plant CTR-009 error in Session 5, not 7; simplify Power BI to 2 pages if needed |
| openpyxl conditional formatting breaks in Excel | High — validation_review.xlsx looks broken | Med — openpyxl formatting quirks are known | Open file in Excel after Session 5 build | Test on small sample before full; fallback: add instructions to manual-format |
| `FinalValue = IF(J2<>"",J2,D2)` formula breaks | Med — reviewers see wrong values | Low — standard IF formula | Open file, edit one ReviewerOverride, verify FinalValue | Write formula string directly via openpyxl; session 5 must include Excel open-and-verify step |
| `source_data/source_business_entities.xlsx` not available for script 00 testing | Med — can't verify BE Load File format | Med — file must be provided by Braden | Check before Session 5 starts | Script 00 can be written even without the file; test with a synthetic 2-row sample |
| LLM proxy unavailable during a build session | High — blocks all LLM work in Sessions 5–6 | Low — proxy has been stable | Test `$env:LITELLM_API_BASE/models` at session start | No offline fallback; contact IT if down |
| coupa_ready.xlsx human gate broken | Critical — undermines core demo claim | Low — logic is straightforward | Approve 3 rows, verify only 3 appear | Enforce with `assert` in script 08 |
| Power BI connection breaks on file path change | Med — dashboard won't refresh | Low — paths are stable | Test refresh after session 6 setup | Document exact paths in README; use absolute paths |
| Git conflict or data loss | High | Very low — single contributor, single branch | `git status` before every commit | Never force-push; always commit before starting a session |
| ~~CTR-014 "TBD" date fails to trigger R001~~ | ~~High~~ | **RESOLVED** — R001 fires on CTR-014 ✓ | — | `is_null_value()` handles "TBD" |
| ~~R006 silently skips CTR-013 auto-renewal~~ | ~~High~~ | **RESOLVED** — clause_check broadened ✓ | — | Fixed in Session 4 |

---

## 9. Most Recent Experiment/Attempt

### What was tried

**Session 4 — `05_run_rules.py` + `06_summarize.py` — written and run 2026-04-21**

**05_run_rules.py:**
- Loads `rules.xlsx` (10 enabled rules) and `extracted_fields.xlsx` (165 rows, 15 contracts)
- Evaluates each rule against each contract's field data
- R010 (confidence below threshold) evaluated per non-null field
- Writes `outputs/risk_signals.xlsx` with severity-colored rows

**06_summarize.py:**
- Reads `contract_catalog.xlsx` + `contract_text/*.txt` + key fields from `extracted_fields.xlsx`
- Calls LiteLLM `gemini/gemini-3-flash-preview` with structured context (key fields + contract text)
- Writes `outputs/summaries.xlsx` (15 rows, wrap-text formatted)

### Expected result

- 21+ risk signals, all expected rules firing on expected contracts
- 15/15 summaries generated without failure
- R001 on CTR-014, R004 on CTR-012, R005 on CTR-010/011, R006 on CTR-013

### Actual result

**Run 1 (rules engine):** 20 signals — R006 missing. Root cause: CTR-013 AutoRenewal = "Successive one-year terms", not "PRESENT". Clause_check equality check on `"PRESENT"` failed to match.

**Fix:** Broadened `clause_check` "present" logic — now fires if value is non-empty AND not in ("NOT_FOUND", "NULL", "NONE", ""). This is correct because a descriptive value still means the clause is present.

**Run 2 (rules engine):** 21 signals — R006 now fires on CTR-013. All expected signals confirmed.

**Run 1 (summarize):** 14/15 — CTR-001 returned None content from LLM.

**Fix:** Added one retry with 2s delay on None response.

**Run 2 (summarize):** 14/15 — CTR-008 returned None content (different contract, same transient issue).

**Run 3 (summarize, with retry fix):** 15/15 — CTR-006 triggered None on first attempt, retry succeeded. All 15 contracts summarized.

### Interpretation

- LLM clause fields (AutoRenewal, LiabilityCap, TerminationClause) should return "PRESENT" or "NOT_FOUND" per schema, but Gemini sometimes returns descriptive text. The rules engine must be tolerant of this — the fix is robust and correct.
- Transient None LLM responses are a model-side issue (likely related to content filtering or streaming edge cases). One retry with a short delay resolves it consistently.
- R010 (low confidence) did NOT fire this run because all low-confidence fields are null/NOT_FOUND — R010 is scoped to non-null fields with low confidence. This is correct behavior.

### Artifacts

- `outputs/risk_signals.xlsx` — 21 rows, committed at `38bc82a`
- `outputs/summaries.xlsx` — 15 rows, committed at `38bc82a`
- `rules.xlsx` — 10 rules, committed at `38bc82a`
- `PROGRESS.md` — Session 4 entry appended, full signal breakdown logged
- `logs/pipeline_latest.log` — full debug trace of final summarize run

---

## 10. Next Hypothesis and Immediate Plan

### Next hypothesis

`07_build_validation.py` can assemble a correctly structured `validation_review.xlsx` from `extracted_fields.xlsx`, `risk_signals.xlsx`, and `summaries.xlsx` — with openpyxl conditional formatting (red/yellow/green), FinalValue formula, and YES/NO dropdown — that renders correctly when opened in Excel on this machine. Similarly, `08_coupa_artifact.py` can correctly filter to `Approved == "YES"` rows and produce `coupa_ready.xlsx`. Script 00 can transform `source_business_entities.xlsx` into the exact Coupa 5-header-row format.

### Why this is highest-leverage

Session 5 produces the two primary demo artifacts: `validation_review.xlsx` (the human review surface Beat 4 of the demo script) and `coupa_ready.xlsx` (the gated Coupa staging artifact Beat 5). Without these, the demo narrative breaks. The validation table is also the most visually complex artifact — openpyxl formatting must render in Excel.

### Step-by-step plan for Session 5

Use this command to start Session 5:
```
claude.cmd /plan "Write and run 07_build_validation.py and 08_coupa_artifact.py per the build guide. Also write 00_build_be_load_file.py per the BE load file spec. Ensure validation_review.xlsx has conditional formatting, FinalValue formula, and YES/NO dropdown on Approved column."
```

**Critical implementation notes for Session 5:**

1. **`07_build_validation.py` joins** — start with every row in `extracted_fields.xlsx`, left-join `risk_signals.xlsx` on `ContractID + FieldTriggered`. Take highest severity where multiple rules fire on the same field.

2. **FinalValue formula** — write as string `=IF(J2<>"",J2,D2)` — column J is `ReviewerOverride`. Adjust row number dynamically for each data row. Column letter mapping must match the final column order exactly.

3. **Conditional formatting** — openpyxl `PatternFill` for red (High), yellow (Medium or Confidence < 0.6), green (Approved = YES). Apply per-row, not via openpyxl's `ConditionalFormattingList` — the latter has known Excel rendering issues.

4. **YES/NO dropdown** — use openpyxl `DataValidation` on the `Approved` column: `type="list"`, `formula1='"YES,NO"'`.

5. **Sheet tabs** — `Review` (main), `Summaries` (from summaries.xlsx), `Risk Signals` (read-only copy from risk_signals.xlsx).

6. **`08_coupa_artifact.py`** — pivot `FinalValue` logic: read `validation_review.xlsx`, filter `Approved == "YES"`, pivot long → wide by `ContractID + FieldName`. Map field names to Coupa columns per build guide section 7.5. Add red warning banner row.

7. **Script 00** — write all cells as `str()` with `number_format = '@'` to prevent Excel auto-formatting of postal codes and IDs. Validate row count after write. See build guide section 6 for exact 5-header-row structure.

8. **Approval checkpoint** — open `validation_review.xlsx` in Excel immediately after generation. Verify: red/yellow rows visible, FinalValue formula resolves, dropdown works on Approved column. Manually approve 3 rows, run script 08, verify only those 3 in `coupa_ready.xlsx`.

9. **Session end** — commit: `git add . && git commit -m "Session 5: Validation table + Coupa artifacts"`

---

## 11. Open Questions

| Question | Why it matters | Blocking? | Who/what resolves it |
|---|---|---|---|
| Will openpyxl conditional formatting render correctly in Excel on Braden's machine? | `validation_review.xlsx` red/yellow/green highlighting is a demo visual | Yes — Session 5 | Test file open in Excel after Session 5 |
| Does the `FinalValue = IF(J2<>"",J2,D2)` formula work after openpyxl write? | Formula is how reviewer corrections auto-resolve without macros | Yes — Session 5 | Session 5 + manual Excel test |
| Is `source_data/source_business_entities.xlsx` available for testing script 00? | Without it, BE Load File script can't be tested end-to-end | Partial — script can be written but not tested | Braden provides file OR Session 5 creates a synthetic 2-row sample for testing |
| Will the Power BI file paths work from `C:\Users\jonesbrade\ai-contracts-poc\outputs\`? | Power BI connections must point to stable paths | Yes — Session 6 | Session 6 setup; document exact paths in README |
| Can Session 6 (orchestrator + Power BI) and Session 7 (cleanup + demo prep) be merged if time is short? | Timeline is tight — Thursday deadline | Yes if session 5 or 6 runs long | Scope Power BI to 2 pages; skip orchestrator flags if time-critical |
| ~~Will `safe_parse_date("TBD")` correctly return None and trigger R001 on CTR-014?~~ | **RESOLVED** — R001 fires on CTR-014 ✓ | — | Confirmed Session 4 |
| ~~Does `MAX_TOKENS_SUMMARY = 500` produce complete summaries?~~ | **RESOLVED** — 15/15 summaries complete ✓ | — | Confirmed Session 4 |
| ~~Will R006 fire on CTR-013 auto-renewal?~~ | **RESOLVED** — R006 fires on CTR-013 ✓ | — | Fixed in Session 4 via clause_check broadening |
| Is Tesseract needed for any demo scenario? | CTR-015 OCR fallback path is untested | No — CTR-015 is a text PDF; demo doesn't require true OCR | Not blocking; note as known limitation in README |

---

*This document reflects verified state as of 2026-04-21, post-Session 4 commit `38bc82a`. Sessions 1–4 complete. Sessions 5–7 remain before Thursday April 24 demo deadline. Previous `HANDOFF.md` and pre-Session-4 `AUDIT_HANDOFF.md` are both stale — this document is authoritative.*
