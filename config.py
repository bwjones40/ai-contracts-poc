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
LITELLM_API_KEY  = os.environ.get("LITELLM_API_KEY",  "")

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
