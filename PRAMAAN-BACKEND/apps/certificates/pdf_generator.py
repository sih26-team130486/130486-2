"""
certificates/pdf_generator.py
ReportLab PDF builder for PRAMAAN Evidence Integrity Certificates.

Generates a professional government-style PDF containing:
  - Certificate header with serial number
  - Document details (filename, case, uploader, upload date)
  - SHA-256 integrity hash (full 64 chars)
  - Verification result and verdict
  - Chain of custody table (all transfers)
  - Diagonal PRAMAAN CERTIFIED watermark
  - Footer with generation timestamp
"""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------------------
# Colour palette — government navy + saffron accent
# ---------------------------------------------------------------------------
NAVY     = colors.HexColor('#0D2137')
SAFFRON  = colors.HexColor('#FF6600')
GREEN_OK = colors.HexColor('#1A7A3E')
RED_FAIL = colors.HexColor('#CC0000')
LIGHT_BG = colors.HexColor('#F5F7FA')
GREY     = colors.HexColor('#6B7280')
WHITE    = colors.white


# ---------------------------------------------------------------------------
# Watermark canvas callback
# ---------------------------------------------------------------------------
def _add_watermark(canv, doc):
    """Draw a diagonal watermark and a thin border on every page."""
    canv.saveState()
    width, height = A4

    # Diagonal text watermark
    canv.setFont('Helvetica-Bold', 52)
    canv.setFillColor(colors.HexColor('#E8EDF2'))
    canv.setStrokeColor(colors.HexColor('#E8EDF2'))
    canv.translate(width / 2, height / 2)
    canv.rotate(45)
    canv.drawCentredString(0, 0, 'PRAMAAN CERTIFIED')

    canv.restoreState()

    # Thin outer border
    canv.saveState()
    canv.setStrokeColor(NAVY)
    canv.setLineWidth(1.5)
    canv.rect(1 * cm, 1 * cm, width - 2 * cm, height - 2 * cm)
    canv.restoreState()


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
def generate_certificate_pdf(
    cert_number: str,
    document,           # Document model instance
    generated_by,       # CustomUser model instance
    verification=None,  # VerificationResult model instance (optional)
    custody_chain=None, # CustodyChain model instance (optional)
    cert_type: str = 'INTEGRITY',
) -> bytes:
    """
    Generate a PDF certificate and return the raw bytes.
    Caller saves to disk.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f'PRAMAAN Certificate {cert_number}',
        author='PRAMAAN Secure Evidence System',
    )

    styles = getSampleStyleSheet()

    # Custom styles
    def style(name, **kwargs):
        return ParagraphStyle(name, parent=styles['Normal'], **kwargs)

    s_title   = style('Title',   fontSize=16, fontName='Helvetica-Bold',
                      textColor=NAVY, alignment=TA_CENTER, spaceAfter=4)
    s_sub     = style('Sub',     fontSize=10, fontName='Helvetica',
                      textColor=GREY, alignment=TA_CENTER, spaceAfter=2)
    s_cert_no = style('CertNo',  fontSize=11, fontName='Helvetica-Bold',
                      textColor=SAFFRON, alignment=TA_CENTER, spaceAfter=6)
    s_section = style('Section', fontSize=11, fontName='Helvetica-Bold',
                      textColor=NAVY, spaceBefore=12, spaceAfter=4)
    s_label   = style('Label',   fontSize=9,  fontName='Helvetica-Bold',
                      textColor=GREY)
    s_value   = style('Value',   fontSize=10, fontName='Helvetica',
                      textColor=colors.black)
    s_hash    = style('Hash',    fontSize=8,  fontName='Courier',
                      textColor=NAVY, backColor=LIGHT_BG,
                      leftIndent=6, rightIndent=6, spaceBefore=2, spaceAfter=2)
    s_verdict_ok  = style('VOK',  fontSize=12, fontName='Helvetica-Bold',
                          textColor=GREEN_OK, alignment=TA_CENTER)
    s_verdict_bad = style('VBAD', fontSize=12, fontName='Helvetica-Bold',
                          textColor=RED_FAIL, alignment=TA_CENTER)
    s_footer  = style('Footer',  fontSize=8, fontName='Helvetica',
                      textColor=GREY, alignment=TA_CENTER)

    story = []

    # ── HEADER ───────────────────────────────────────────────────────────────
    story.append(Paragraph('GOVERNMENT OF INDIA', s_sub))
    story.append(Paragraph('PRAMAAN &mdash; SECURE DIGITAL EVIDENCE MANAGEMENT SYSTEM', s_title))
    story.append(Paragraph('Ministry of Home Affairs | National Police Informatics Organisation', s_sub))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width='100%', thickness=2, color=NAVY))
    story.append(Spacer(1, 0.2 * cm))

    cert_type_labels = {
        'INTEGRITY':     'DIGITAL INTEGRITY CERTIFICATE',
        'CUSTODY_CHAIN': 'CHAIN OF CUSTODY CERTIFICATE',
        'COURT_EXPORT':  'COURT SUBMISSION CERTIFICATE',
    }
    story.append(Paragraph(cert_type_labels.get(cert_type, 'EVIDENCE CERTIFICATE'), s_title))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(f'Certificate No: {cert_number}', s_cert_no))
    story.append(HRFlowable(width='100%', thickness=1, color=SAFFRON))
    story.append(Spacer(1, 0.3 * cm))

    # ── SECTION 1: Document Details ───────────────────────────────────────────
    story.append(Paragraph('1. DOCUMENT DETAILS', s_section))

    upload_date = document.uploaded_at.strftime('%d %b %Y, %I:%M %p IST') if document.uploaded_at else '—'
    uploader_name = (
        document.uploader.full_name or document.uploader.username
    ) if document.uploader else '—'

    doc_data = [
        ['Field', 'Value'],
        ['Document Name',  document.filename],
        ['Case ID',        document.case_id or '—'],
        ['Document Type',  document.file_type or '—'],
        ['File Size',      document.file_size_display],
        ['Uploaded By',    uploader_name],
        ['Upload Date',    upload_date],
        ['Document Status', document.get_status_display()],
    ]

    doc_table = Table(doc_data, colWidths=[5 * cm, 12 * cm])
    doc_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',    (0, 0), (-1, 0), WHITE),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0), 9),
        ('BACKGROUND',   (0, 1), (0, -1), LIGHT_BG),
        ('FONTNAME',     (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 1), (-1, -1), 9),
        ('GRID',         (0, 0), (-1, -1), 0.5, colors.HexColor('#DDE3EA')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ('LEFTPADDING',  (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING',   (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 5),
    ]))
    story.append(doc_table)
    story.append(Spacer(1, 0.3 * cm))

    # ── SECTION 2: Integrity Verification ────────────────────────────────────
    story.append(Paragraph('2. INTEGRITY VERIFICATION (SHA-256)', s_section))
    story.append(Paragraph('Original SHA-256 Hash (stored at upload):', s_label))
    story.append(Paragraph(document.sha256_hash, s_hash))
    story.append(Spacer(1, 0.2 * cm))

    if verification:
        verified_date = verification.verified_at.strftime('%d %b %Y, %I:%M %p IST')
        verifier_name = (
            verification.verified_by.full_name or verification.verified_by.username
        ) if verification.verified_by else '—'

        story.append(Paragraph('Computed SHA-256 Hash (at verification time):', s_label))
        story.append(Paragraph(verification.computed_hash, s_hash))
        story.append(Spacer(1, 0.2 * cm))

        ver_data = [
            ['Field', 'Value'],
            ['Verified By',   verifier_name],
            ['Verified At',   verified_date],
            ['Hash Match',    'YES — Hashes Identical' if not verification.is_tampered
                              else 'NO — Hashes Differ (TAMPER DETECTED)'],
        ]
        ver_table = Table(ver_data, colWidths=[5 * cm, 12 * cm])
        ver_table.setStyle(TableStyle([
            ('BACKGROUND',   (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR',    (0, 0), (-1, 0), WHITE),
            ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',     (0, 0), (-1, -1), 9),
            ('BACKGROUND',   (0, 1), (0, -1), LIGHT_BG),
            ('FONTNAME',     (0, 1), (0, -1), 'Helvetica-Bold'),
            ('GRID',         (0, 0), (-1, -1), 0.5, colors.HexColor('#DDE3EA')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
            ('LEFTPADDING',  (0, 0), (-1, -1), 8),
            ('TOPPADDING',   (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 5),
            # Highlight the hash match row
            ('TEXTCOLOR',    (1, 3), (1, 3),
             GREEN_OK if not verification.is_tampered else RED_FAIL),
            ('FONTNAME',     (1, 3), (1, 3), 'Helvetica-Bold'),
        ]))
        story.append(ver_table)
        story.append(Spacer(1, 0.3 * cm))

        # Verdict banner
        if verification.is_tampered:
            story.append(Paragraph('[TAMPERED] INTEGRITY COMPROMISED — Evidence may have been altered', s_verdict_bad))
        else:
            story.append(Paragraph('[VERIFIED] INTEGRITY CONFIRMED — Evidence is authentic and unaltered', s_verdict_ok))
    else:
        story.append(Paragraph('[NOT YET VERIFIED]', s_sub))

    story.append(Spacer(1, 0.3 * cm))

    # ── SECTION 3: Chain of Custody ───────────────────────────────────────────
    story.append(Paragraph('3. CHAIN OF CUSTODY', s_section))

    if custody_chain:
        current_holder = (
            custody_chain.current_holder.full_name
            if custody_chain.current_holder else '—'
        )
        story.append(Paragraph(
            f'Current Holder: <b>{current_holder}</b> &nbsp;|&nbsp; '
            f'Location: <b>{custody_chain.current_location or "—"}</b> &nbsp;|&nbsp; '
            f'Status: <b>{custody_chain.get_status_display()}</b>',
            style('ChainMeta', fontSize=9, fontName='Helvetica', textColor=NAVY)
        ))
        story.append(Spacer(1, 0.2 * cm))

        transfers = custody_chain.transfers.order_by('initiated_at')
        if transfers.exists():
            coc_data = [['#', 'From', 'To', 'Location', 'Status', 'Date']]
            for i, t in enumerate(transfers, 1):
                frm  = t.from_user.full_name if t.from_user else '—'
                to   = t.to_user.full_name if t.to_user else '—'
                date = t.initiated_at.strftime('%d %b %Y')
                coc_data.append([
                    str(i), frm, to, t.to_location or '—',
                    t.get_status_display(), date
                ])

            coc_table = Table(
                coc_data,
                colWidths=[0.7*cm, 3.5*cm, 3.5*cm, 3.5*cm, 2.5*cm, 2.5*cm]
            )
            coc_table.setStyle(TableStyle([
                ('BACKGROUND',   (0, 0), (-1, 0), NAVY),
                ('TEXTCOLOR',    (0, 0), (-1, 0), WHITE),
                ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',     (0, 0), (-1, -1), 8),
                ('GRID',         (0, 0), (-1, -1), 0.5, colors.HexColor('#DDE3EA')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
                ('LEFTPADDING',  (0, 0), (-1, -1), 5),
                ('TOPPADDING',   (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
                ('ALIGN',        (0, 0), (0, -1), 'CENTER'),
            ]))
            story.append(coc_table)
        else:
            story.append(Paragraph('No transfers recorded. Evidence registered but not yet transferred.', s_value))
    else:
        story.append(Paragraph('No custody chain registered for this document.', s_value))

    story.append(Spacer(1, 0.4 * cm))

    # ── SECTION 4: Certificate Details ───────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    story.append(Spacer(1, 0.2 * cm))

    gen_name = generated_by.full_name or generated_by.username
    gen_role = generated_by.get_role_display()
    gen_time = datetime.now().strftime('%d %b %Y, %I:%M %p IST')

    cert_meta = [
        ['Certificate Number', cert_number,
         'Certificate Type',   cert_type_labels.get(cert_type, cert_type)],
        ['Generated By',       f'{gen_name} [{gen_role}]',
         'Generated At',       gen_time],
        ['Document ID',        str(document.id),
         'System',             'PRAMAAN v1.0 — SIH PS 26190'],
    ]
    meta_table = Table(cert_meta, colWidths=[4*cm, 7.5*cm, 4*cm, 7.5*cm])

    # Removed colSpan usage since it causes ReportLab issues — simple 4-col layout
    meta_table.setStyle(TableStyle([
        ('FONTNAME',  (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',  (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (0, -1), GREY),
        ('TEXTCOLOR', (2, 0), (2, -1), GREY),
        ('BACKGROUND',(0, 0), (-1, -1), LIGHT_BG),
        ('GRID',      (0, 0), (-1, -1), 0.3, colors.HexColor('#DDE3EA')),
        ('LEFTPADDING',(0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.3 * cm))

    # ── FOOTER ───────────────────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=0.5, color=GREY))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(
        'This certificate is computer-generated by the PRAMAAN Secure Digital Evidence Management System. '
        'Any alteration to this document renders it invalid. '
        'SHA-256 cryptographic hash is used to ensure document integrity.',
        s_footer
    ))
    story.append(Paragraph(
        f'Certificate No: {cert_number} | Generated: {gen_time} | '
        f'System: PRAMAAN v1.0 | SIH PS 26190',
        s_footer
    ))

    # Build PDF
    doc.build(story, onFirstPage=_add_watermark, onLaterPages=_add_watermark)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
