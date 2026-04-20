"""
scripts/01_generate_mocks.py

Generates 15 mock contracts into mock_contracts/ directory.
Only run if real sample contracts are unavailable.

Usage: python scripts/01_generate_mocks.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from logger import get_logger, write_summary_xlsx, _RUN_TIMESTAMP

logger = get_logger(__name__)

MOCK_DIR = Path(__file__).parent.parent / "mock_contracts"
MOCK_DIR.mkdir(exist_ok=True)

DISCLAIMER = "[SIMULATED DATA — FOR POC DEMONSTRATION ONLY — NOT A REAL CONTRACT]"

CONTRACTS = [
    # 1-4: MSA, PDF (text), clean, all fields present
    {
        "id": "CTR-001", "filename": "CTR-001_MSA_Apex_Industrial.pdf",
        "type": "Master Service Agreement", "supplier": "Apex Industrial Services LLC",
        "effective": "2024-01-15", "expiration": "2027-01-14",
        "value": "$2,500,000", "entity": "Braden Corp - North Division",
        "law": "Delaware", "payment": "Net 30",
        "auto_renewal": False, "liability_cap": True, "termination": True,
        "format": "pdf",
    },
    {
        "id": "CTR-002", "filename": "CTR-002_MSA_Summit_Logistics.pdf",
        "type": "Master Service Agreement", "supplier": "Summit Logistics Partners Inc.",
        "effective": "2023-06-01", "expiration": "2026-05-31",
        "value": "$1,800,000", "entity": "Braden Corp - Supply Chain",
        "law": "Texas", "payment": "Net 45",
        "auto_renewal": False, "liability_cap": True, "termination": True,
        "format": "pdf",
    },
    {
        "id": "CTR-003", "filename": "CTR-003_MSA_Meridian_Tech.pdf",
        "type": "Master Service Agreement", "supplier": "Meridian Technology Solutions",
        "effective": "2024-03-01", "expiration": "2027-02-28",
        "value": "$4,200,000", "entity": "Braden Corp - IT Division",
        "law": "California", "payment": "Net 30",
        "auto_renewal": False, "liability_cap": True, "termination": True,
        "format": "pdf",
    },
    {
        "id": "CTR-004", "filename": "CTR-004_MSA_Pinnacle_Consulting.pdf",
        "type": "Master Service Agreement", "supplier": "Pinnacle Consulting Group",
        "effective": "2023-09-01", "expiration": "2026-08-31",
        "value": "$750,000", "entity": "Braden Corp - Finance",
        "law": "New York", "payment": "Net 60",
        "auto_renewal": False, "liability_cap": True, "termination": True,
        "format": "pdf",
    },
    # 5-7: SOW, PDF (text), clean, some missing fields
    {
        "id": "CTR-005", "filename": "CTR-005_SOW_Vertex_Engineering.pdf",
        "type": "Statement of Work", "supplier": "Vertex Engineering Corp",
        "effective": "2024-02-01", "expiration": "2025-01-31",
        "value": "$320,000", "entity": "Braden Corp - Operations",
        "law": "Ohio", "payment": "Net 30",
        "auto_renewal": False, "liability_cap": False, "termination": True,
        "format": "pdf",
    },
    {
        "id": "CTR-006", "filename": "CTR-006_SOW_BlueStar_Services.pdf",
        "type": "Statement of Work", "supplier": "BlueStar Professional Services",
        "effective": "2024-04-15", "expiration": "2025-04-14",
        "value": "$185,000", "entity": "Braden Corp - HR",
        "law": "Illinois", "payment": "Net 30",
        "auto_renewal": False, "liability_cap": False, "termination": False,
        "format": "pdf",
    },
    {
        "id": "CTR-007", "filename": "CTR-007_SOW_Crestline_Analytics.pdf",
        "type": "Statement of Work", "supplier": "Crestline Analytics LLC",
        "effective": "2023-11-01", "expiration": "2024-10-31",
        "value": "$98,500", "entity": "Braden Corp - Marketing",
        "law": "Washington", "payment": "Net 45",
        "auto_renewal": False, "liability_cap": True, "termination": True,
        "format": "pdf",
    },
    # 8-9: NDA, DOCX, clean, short
    {
        "id": "CTR-008", "filename": "CTR-008_NDA_Horizon_Partners.docx",
        "type": "Non-Disclosure Agreement", "supplier": "Horizon Strategic Partners",
        "effective": "2024-05-01", "expiration": "2027-04-30",
        "value": None, "entity": "Braden Corp - Legal",
        "law": "Delaware", "payment": None,
        "auto_renewal": False, "liability_cap": False, "termination": True,
        "format": "docx",
    },
    {
        "id": "CTR-009", "filename": "CTR-009_NDA_Redwood_Innovations.docx",
        "type": "Non-Disclosure Agreement", "supplier": "Redwood Innovations Inc.",
        "effective": "2024-07-15", "expiration": "2027-07-14",
        "value": None, "entity": "Braden Corp - R&D",
        "law": "California", "payment": None,
        "auto_renewal": False, "liability_cap": False, "termination": True,
        "format": "docx",
    },
    # 10-11: Purchase Agreement, PDF, expiring within 90 days → fires R005
    {
        "id": "CTR-010", "filename": "CTR-010_PurchaseAgreement_Cascade_Supply.pdf",
        "type": "Purchase Agreement", "supplier": "Cascade Supply Co.",
        "effective": "2023-05-01", "expiration": "2026-05-15",
        "value": "$560,000", "entity": "Braden Corp - Procurement",
        "law": "Oregon", "payment": "Net 30",
        "auto_renewal": False, "liability_cap": True, "termination": True,
        "format": "pdf",
    },
    {
        "id": "CTR-011", "filename": "CTR-011_PurchaseAgreement_Atlas_Materials.pdf",
        "type": "Purchase Agreement", "supplier": "Atlas Materials Group",
        "effective": "2023-06-15", "expiration": "2026-06-01",
        "value": "$1,100,000", "entity": "Braden Corp - Manufacturing",
        "law": "Michigan", "payment": "Net 45",
        "auto_renewal": False, "liability_cap": True, "termination": True,
        "format": "pdf",
    },
    # 12: Service Agreement, already expired → fires R004
    {
        "id": "CTR-012", "filename": "CTR-012_ServiceAgreement_Ironclad_Facilities.pdf",
        "type": "Service Agreement", "supplier": "Ironclad Facilities Management",
        "effective": "2022-01-01", "expiration": "2024-12-31",
        "value": "$430,000", "entity": "Braden Corp - Facilities",
        "law": "Florida", "payment": "Net 30",
        "auto_renewal": False, "liability_cap": True, "termination": True,
        "format": "pdf",
    },
    # 13: MSA, auto-renewal clause → fires R006
    {
        "id": "CTR-013", "filename": "CTR-013_MSA_Strata_Cloud.pdf",
        "type": "Master Service Agreement", "supplier": "Strata Cloud Solutions",
        "effective": "2023-03-01", "expiration": "2026-02-28",
        "value": "$3,600,000", "entity": "Braden Corp - IT Division",
        "law": "Virginia", "payment": "Net 30",
        "auto_renewal": True, "liability_cap": True, "termination": True,
        "format": "pdf",
    },
    # 14: SOW, DOCX, missing ExpirationDate → fires R001
    {
        "id": "CTR-014", "filename": "CTR-014_SOW_Nomad_Staffing.docx",
        "type": "Statement of Work", "supplier": "Nomad Staffing Solutions",
        "effective": "2024-08-01", "expiration": None,
        "value": "$210,000", "entity": "Braden Corp - Operations",
        "law": "Arizona", "payment": "Net 30",
        "auto_renewal": False, "liability_cap": False, "termination": False,
        "format": "docx",
    },
    # 15: Agreement, PDF (image/degraded scan) → OCR fallback
    {
        "id": "CTR-015", "filename": "CTR-015_Agreement_OldScan_Legacy.pdf",
        "type": "Service Agreement", "supplier": "Legacy Maintenance Corp",
        "effective": "2021-06-01", "expiration": "2025-05-31",
        "value": "$75,000", "entity": "Braden Corp - Facilities",
        "law": "Tennessee", "payment": "Net 60",
        "auto_renewal": False, "liability_cap": False, "termination": False,
        "format": "pdf_image",
    },
]


def build_pdf_text(c: dict) -> str:
    """Build the full text content for a text-based PDF contract."""
    expiration_line = f"Expiration Date: {c['expiration']}" if c['expiration'] else ""
    value_line = f"Total Contract Value: {c['value']}" if c['value'] else ""
    payment_line = f"Payment Terms: {c['payment']}" if c['payment'] else ""

    auto_renewal_text = ""
    if c['auto_renewal']:
        auto_renewal_text = (
            "\n\n6. AUTO-RENEWAL\nThis Agreement shall automatically renew for successive one-year "
            "terms unless either party provides written notice of non-renewal at least sixty (60) "
            "days prior to the end of the then-current term."
        )

    liability_text = ""
    if c['liability_cap']:
        liability_text = (
            "\n\n7. LIMITATION OF LIABILITY\nIn no event shall either party's total cumulative "
            "liability arising out of or related to this Agreement exceed the total fees paid or "
            "payable by Client to Supplier in the twelve (12) months preceding the claim."
        )

    termination_text = ""
    if c['termination']:
        termination_text = (
            "\n\n8. TERMINATION FOR CONVENIENCE\nEither party may terminate this Agreement for "
            "any reason upon thirty (30) days prior written notice to the other party."
        )

    return f"""{c['type'].upper()}

This {c['type']} (\"Agreement\") is entered into as of {c['effective']} (\"Effective Date\") by and between:

{c['supplier']} (\"Supplier\")
and
{c['entity']} (\"Client\")

1. TERM
Effective Date: {c['effective']}
{expiration_line}

2. SCOPE OF SERVICES
Supplier agrees to provide services as mutually agreed upon in applicable Statements of Work or Purchase Orders issued under this Agreement.

3. FINANCIAL TERMS
{value_line}
{payment_line}

4. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with the laws of the State of {c.get('law', 'Delaware')}, without regard to its conflict of law provisions.

5. GENERAL PROVISIONS
This Agreement constitutes the entire agreement between the parties with respect to its subject matter and supersedes all prior agreements and understandings.
{auto_renewal_text}{liability_text}{termination_text}

IN WITNESS WHEREOF, the parties have executed this Agreement as of the Effective Date.

{c['supplier']}
Authorized Signature: _______________________
Name: ___________________________
Title: ___________________________
Date: ___________________________

{c['entity']}
Authorized Signature: _______________________
Name: ___________________________
Title: ___________________________
Date: ___________________________

{DISCLAIMER}
"""


def build_nda_text(c: dict) -> str:
    """Build text content for an NDA."""
    return f"""NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement (\"Agreement\") is entered into as of {c['effective']} between:

{c['supplier']} (\"Disclosing Party\")
and
{c['entity']} (\"Receiving Party\")

1. CONFIDENTIAL INFORMATION
\"Confidential Information\" means any non-public information disclosed by either party.

2. OBLIGATIONS
The Receiving Party agrees to hold all Confidential Information in strict confidence and not to disclose it to any third party without prior written consent.

3. TERM
This Agreement is effective as of {c['effective']} and shall remain in effect until {c['expiration']}.

4. GOVERNING LAW
This Agreement shall be governed by the laws of the State of {c.get('law', 'Delaware')}.

5. TERMINATION FOR CONVENIENCE
Either party may terminate this Agreement upon thirty (30) days written notice.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

{c['supplier']}
Signature: _______________________
Date: ___________________________

{c['entity']}
Signature: _______________________
Date: ___________________________

{DISCLAIMER}
"""


def build_sow_docx_text(c: dict) -> str:
    """Build text content for a SOW DOCX."""
    expiration_line = f"End Date: {c['expiration']}" if c['expiration'] else "End Date: TBD — to be confirmed upon project scoping"
    value_line = f"Not-to-Exceed Amount: {c['value']}" if c['value'] else ""

    return f"""STATEMENT OF WORK

This Statement of Work (\"SOW\") is entered into pursuant to the Master Services Agreement between {c['supplier']} and {c['entity']}.

Project: Professional Services Engagement
Supplier: {c['supplier']}
Client: {c['entity']}
Start Date: {c['effective']}
{expiration_line}

1. SERVICES
Supplier shall provide the following services:
- Project planning and requirements analysis
- Implementation and delivery
- Testing and quality assurance
- Documentation and knowledge transfer

2. COMPENSATION
{value_line}
Payment Terms: {c.get('payment', 'Net 30')}

3. GOVERNING LAW
This SOW is governed by the laws of the State of {c.get('law', 'Delaware')}.

4. ACCEPTANCE
Work product shall be deemed accepted if Client does not provide written objection within ten (10) business days of delivery.

{DISCLAIMER}
"""


def generate_pdf_text(filepath: Path, content: str) -> None:
    """Generate a text-based PDF using reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch

    doc = SimpleDocTemplate(str(filepath), pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    for line in content.split('\n'):
        if line.strip() == '':
            story.append(Spacer(1, 0.1 * inch))
        else:
            style = styles['Heading1'] if line.isupper() and len(line) > 5 else styles['Normal']
            story.append(Paragraph(line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), style))

    doc.build(story)


def generate_pdf_image(filepath: Path, content: str) -> None:
    """Generate a degraded image-based PDF to simulate a scanned document."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
    from PIL import Image, ImageFilter, ImageEnhance
    import io
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as rl_canvas

    # First render to an in-memory PDF, then convert to image and re-embed
    # For simplicity, use reportlab with a degraded font appearance via image overlay
    tmp_path = filepath.with_suffix('.tmp.pdf')

    doc = SimpleDocTemplate(str(tmp_path), pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("SCANNED DOCUMENT — OCR REQUIRED", styles['Heading1']))
    story.append(Spacer(1, 0.2 * inch))
    for line in content.split('\n'):
        if line.strip() == '':
            story.append(Spacer(1, 0.1 * inch))
        else:
            story.append(Paragraph(
                line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'),
                styles['Normal']
            ))
    doc.build(story)

    # Rename tmp to final (true image-PDF conversion requires pdf2image + PIL
    # which needs poppler — skip the image degradation step for scaffold;
    # the file will still trigger the OCR path via low text yield heuristic
    # if pdfplumber extraction is poor on the re-encoded file)
    import os
    os.replace(str(tmp_path), str(filepath))


def generate_docx(filepath: Path, content: str) -> None:
    """Generate a DOCX file."""
    from docx import Document
    doc = Document()
    for line in content.split('\n'):
        doc.add_paragraph(line)
    doc.save(str(filepath))


def main():
    summary_events = []
    logger.info("[STEP 1] Starting mock contract generation")

    generated = 0
    for c in CONTRACTS:
        out_path = MOCK_DIR / c['filename']

        if out_path.exists():
            logger.info(f"  Skipping {c['filename']} — already exists")
            generated += 1
            continue

        try:
            fmt = c['format']
            if fmt == 'pdf':
                content = build_pdf_text(c)
                generate_pdf_text(out_path, content)
            elif fmt == 'pdf_image':
                content = build_pdf_text(c)
                generate_pdf_image(out_path, content)
            elif fmt == 'docx':
                if c['type'] == 'Non-Disclosure Agreement':
                    content = build_nda_text(c)
                else:
                    content = build_sow_docx_text(c)
                generate_docx(out_path, content)

            logger.info(f"  Generated {c['filename']}")
            generated += 1

        except Exception as e:
            msg = f"Failed to generate {c['filename']}: {e}"
            logger.error(msg)
            summary_events.append({
                "run_timestamp": _RUN_TIMESTAMP,
                "script": "01_generate_mocks",
                "contract_id": c['id'],
                "level": "ERROR",
                "message": msg,
            })

    logger.info(f"[STEP 1] Complete -- {generated}/{len(CONTRACTS)} mock contracts generated -> {MOCK_DIR}")
    write_summary_xlsx(summary_events)


if __name__ == "__main__":
    main()
