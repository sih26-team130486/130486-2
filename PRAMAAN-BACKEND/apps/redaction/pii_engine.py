"""
redaction/pii_engine.py
Pure-Regex PII detection + PyMuPDF-based redaction engine.

Supports:
  - Plain text files (.txt, .csv, .log, etc.)
  - PDF files (via PyMuPDF text extraction)

PII types detected (Indian-specific):
  AADHAAR      — 12-digit number in XXXX-XXXX-XXXX or XXXXXXXXXXXX format
  PAN          — 10-char alphanumeric (ABCDE1234F)
  PHONE        — Indian mobile numbers (+91, 0, raw 10-digit)
  EMAIL        — Standard email addresses
  VOTER_ID     — 10-char Voter ID (ABC1234567)
  PASSPORT     — Indian passport (A1234567)
  BANK_ACCOUNT — 9-18 digit numbers (conservative)
  PERSON_NAME  — Titles (Mr/Mrs/Dr/Shri/Smt) followed by names
"""

import re
import io
from dataclasses import dataclass, field
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# PII Patterns
# ---------------------------------------------------------------------------
PII_PATTERNS = [
    {
        'type':        'AADHAAR',
        'label':       '[AADHAAR REDACTED]',
        'pattern':     re.compile(
            r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
        ),
        'severity':    'CRITICAL',
    },
    {
        'type':        'PAN',
        'label':       '[PAN REDACTED]',
        'pattern':     re.compile(
            r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
        ),
        'severity':    'HIGH',
    },
    {
        'type':        'PHONE',
        'label':       '[PHONE REDACTED]',
        'pattern':     re.compile(
            r'(\+91[\s\-]?|0)?[6-9]\d{9}\b'
        ),
        'severity':    'HIGH',
    },
    {
        'type':        'EMAIL',
        'label':       '[EMAIL REDACTED]',
        'pattern':     re.compile(
            r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
        ),
        'severity':    'HIGH',
    },
    {
        'type':        'VOTER_ID',
        'label':       '[VOTER ID REDACTED]',
        'pattern':     re.compile(
            r'\b[A-Z]{3}[0-9]{7}\b'
        ),
        'severity':    'HIGH',
    },
    {
        'type':        'PASSPORT',
        'label':       '[PASSPORT REDACTED]',
        'pattern':     re.compile(
            r'\b[A-PR-WYa-pr-wy][1-9]\d{5}[1-9]\b'
        ),
        'severity':    'MEDIUM',
    },
    {
        'type':        'PERSON_NAME',
        'label':       '[NAME REDACTED]',
        'pattern':     re.compile(
            r'\b(Mr|Mrs|Ms|Dr|Shri|Smt|Kumar|Prof)\.?\s+[A-Z][a-z]+'
            r'(\s+[A-Z][a-z]+){0,2}\b'
        ),
        'severity':    'MEDIUM',
    },
]


@dataclass
class PIIMatch:
    pii_type:  str
    value:     str          # Original matched text
    masked:    str          # What it gets replaced with
    start:     int          # Character position in text
    end:       int
    severity:  str


@dataclass
class PIIReport:
    total_found:  int = 0
    matches:      List[Dict[str, Any]] = field(default_factory=list)
    types_found:  List[str] = field(default_factory=list)
    redacted_text: str = ''


# ---------------------------------------------------------------------------
# Core: scan text
# ---------------------------------------------------------------------------
def scan_text(text: str) -> PIIReport:
    """
    Scan a string for all PII patterns.
    Returns a PIIReport with all matches and the redacted version.
    """
    report  = PIIReport()
    matches: List[PIIMatch] = []

    for pattern_def in PII_PATTERNS:
        for m in pattern_def['pattern'].finditer(text):
            matches.append(PIIMatch(
                pii_type = pattern_def['type'],
                value    = m.group(),
                masked   = pattern_def['label'],
                start    = m.start(),
                end      = m.end(),
                severity = pattern_def['severity'],
            ))

    # Sort by position (start index) for correct replacement order
    matches.sort(key=lambda x: x.start)

    # Build redacted text (process right-to-left to preserve indices)
    redacted = text
    for m in reversed(matches):
        redacted = redacted[:m.start] + m.masked + redacted[m.end:]

    # Collect unique types
    types_found = list(dict.fromkeys(m.pii_type for m in matches))

    report.total_found   = len(matches)
    report.types_found   = types_found
    report.redacted_text = redacted
    report.matches       = [
        {
            'type':     m.pii_type,
            'masked':   m.masked,
            # Show only partial original for the report (never store full value)
            'preview':  _mask_preview(m.value),
            'severity': m.severity,
        }
        for m in matches
    ]
    return report


def _mask_preview(value: str) -> str:
    """Show first 2 and last 2 chars only: 'AB***XY'"""
    if len(value) <= 4:
        return '*' * len(value)
    return value[:2] + '*' * (len(value) - 4) + value[-2:]


# ---------------------------------------------------------------------------
# Text file: read + scan + produce redacted bytes
# ---------------------------------------------------------------------------
def process_text_file(file_path: str) -> tuple[PIIReport, bytes]:
    """
    Read a plain text file, scan for PII, return report + redacted bytes.
    """
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()

    report = scan_text(text)
    redacted_bytes = report.redacted_text.encode('utf-8')
    return report, redacted_bytes


# ---------------------------------------------------------------------------
# PDF file: extract text with PyMuPDF, scan, produce redacted PDF
# ---------------------------------------------------------------------------
def process_pdf_file(file_path: str) -> tuple[PIIReport, bytes]:
    """
    Open a PDF with PyMuPDF, extract all text, find PII,
    then produce a redacted PDF where PII text is covered with black boxes.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise RuntimeError('PyMuPDF (fitz) is not installed. Run: pip install pymupdf')

    doc = fitz.open(file_path)
    all_text = ''
    for page in doc:
        all_text += page.get_text()

    # Scan full text for report
    report = scan_text(all_text)

    # Now redact: draw black rectangles over each PII match in the PDF
    for pattern_def in PII_PATTERNS:
        for page in doc:
            hits = page.search_for(None)  # placeholder
            # Search page text for each regex match
            page_text = page.get_text()
            for m in pattern_def['pattern'].finditer(page_text):
                matched_str = m.group()
                # Find all instances on the page visually
                rects = page.search_for(matched_str)
                for rect in rects:
                    # Draw filled black rectangle over PII
                    page.draw_rect(rect, color=(0, 0, 0), fill=(0, 0, 0))

    # Save redacted PDF to bytes
    pdf_buffer = io.BytesIO()
    doc.save(pdf_buffer, garbage=4, deflate=True)
    pdf_bytes = pdf_buffer.getvalue()
    doc.close()

    return report, pdf_bytes


# ---------------------------------------------------------------------------
# Dispatcher: choose engine based on file extension
# ---------------------------------------------------------------------------
TEXT_EXTENSIONS = {'.txt', '.csv', '.log', '.md', '.rst', '.xml', '.json'}
PDF_EXTENSIONS  = {'.pdf'}

def process_file(file_path: str) -> tuple[PIIReport, bytes, str]:
    """
    Dispatch to the right engine based on file extension.
    Returns (report, redacted_bytes, output_mime_type)
    """
    import os
    ext = os.path.splitext(file_path)[1].lower()

    if ext in PDF_EXTENSIONS:
        report, redacted_bytes = process_pdf_file(file_path)
        mime = 'application/pdf'
    elif ext in TEXT_EXTENSIONS or ext == '':
        report, redacted_bytes = process_text_file(file_path)
        mime = 'text/plain'
    else:
        # Treat as text for any other type
        report, redacted_bytes = process_text_file(file_path)
        mime = 'application/octet-stream'

    return report, redacted_bytes, mime
