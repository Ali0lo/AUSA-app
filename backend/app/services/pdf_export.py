"""
PDF Export Generation Service for AUSA Platform.
Renders clean, styled PDF documents containing student academic profiles, target program checklists,
and drafted motivation letters using ReportLab.
"""

import io
from datetime import datetime, timezone
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_application_dossier_pdf(
    student_data: Dict[str, Any],
    program_data: Dict[str, Any],
    motivation_letter: str,
) -> bytes:
    """
    Generate a professional binary PDF application dossier containing student metrics,
    target program requirements, financial summary, and formatted motivation letter.

    Args:
        student_data: Dictionary containing student profile fields (email, gpa, ielts, degree_level, etc.)
        program_data: Dictionary containing program requirements (university_name, program_name, tuition_fee, etc.)
        motivation_letter: Drafted text content for statement of purpose / motivation letter.

    Returns:
        bytes: Binary PDF content stream.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "DossierTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DossierSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=10,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=6,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "DossierBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.white,
    )

    letter_text_style = ParagraphStyle(
        "LetterBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("AUSA — Official Application Summary & Dossier", title_style))
    elements.append(Paragraph("AI University & Scholarship Advisor | Verified Academic Candidate Profile", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

    # 2. Candidate & Target Program Summary Table
    elements.append(Paragraph("Candidate & Target University Details", section_heading))

    candidate_email = str(student_data.get("email", "Candidate Student"))
    degree_level = str(student_data.get("degree_level", "Master")).title()
    field_of_study = str(student_data.get("field_of_study", "Computer Science"))

    univ_name = str(program_data.get("university_name", "Target University"))
    prog_name = str(program_data.get("program_name", "Degree Program"))
    country = str(program_data.get("country", "International"))
    deadline = str(program_data.get("deadline", "Upcoming Enrollment Cycle"))

    summary_table_data = [
        [
            Paragraph("<b>Applicant Email:</b>", body_style),
            Paragraph(candidate_email, body_style),
            Paragraph("<b>Target Institution:</b>", body_style),
            Paragraph(f"<b>{univ_name}</b>", body_style),
        ],
        [
            Paragraph("<b>Degree Level:</b>", body_style),
            Paragraph(degree_level, body_style),
            Paragraph("<b>Degree Program:</b>", body_style),
            Paragraph(prog_name, body_style),
        ],
        [
            Paragraph("<b>Field of Study:</b>", body_style),
            Paragraph(field_of_study, body_style),
            Paragraph("<b>Destination Country:</b>", body_style),
            Paragraph(country, body_style),
        ],
        [
            Paragraph("<b>Date Generated:</b>", body_style),
            Paragraph(datetime.now(timezone.utc).strftime("%Y-%m-%d"), body_style),
            Paragraph("<b>Application Deadline:</b>", body_style),
            Paragraph(deadline, body_style),
        ],
    ]

    summary_table = Table(summary_table_data, colWidths=[1.4 * inch, 2.2 * inch, 1.4 * inch, 2.5 * inch])
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 8))

    # 3. Academic & Financial Checklist Table
    elements.append(Paragraph("Academic & Financial Requirements Checklist", section_heading))

    gpa_val = f"{student_data.get('gpa', 3.5):.2f}" if student_data.get("gpa") else "N/A"
    ielts_val = f"{student_data.get('ielts', 7.0):.1f}" if student_data.get("ielts") else "N/A"
    toefl_val = str(student_data.get("toefl")) if student_data.get("toefl") else "N/A"

    tuition_val = f"${program_data.get('tuition_fee', 0.0):,.2f} USD" if program_data.get("tuition_fee") is not None else "Tuition Free"
    dim_req = str(program_data.get("dim_score_required", "Not Applicable"))
    blocked_acc = f"€{program_data.get('blocked_account_eur', 11208.0):,.2f}" if program_data.get("blocked_account_eur") else "Not Required"

    checklist_table_data = [
        [
            Paragraph("Academic Metric", table_header_style),
            Paragraph("Student Score", table_header_style),
            Paragraph("Financial / Visa Item", table_header_style),
            Paragraph("Requirement Status", table_header_style),
        ],
        [
            Paragraph("Grade Point Average (GPA)", body_style),
            Paragraph(f"<b>{gpa_val}</b> / 4.0", body_style),
            Paragraph("Annual Tuition Fee", body_style),
            Paragraph(tuition_val, body_style),
        ],
        [
            Paragraph("English Proficiency (IELTS)", body_style),
            Paragraph(f"<b>{ielts_val}</b>", body_style),
            Paragraph("German Visa Blocked Account", body_style),
            Paragraph(blocked_acc, body_style),
        ],
        [
            Paragraph("English Proficiency (TOEFL)", body_style),
            Paragraph(toefl_val, body_style),
            Paragraph("DIM Entrance Exam Score", body_style),
            Paragraph(dim_req, body_style),
        ],
    ]

    checklist_table = Table(checklist_table_data, colWidths=[2.0 * inch, 1.6 * inch, 2.0 * inch, 1.9 * inch])
    checklist_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    elements.append(checklist_table)
    elements.append(Spacer(1, 10))

    # 4. Motivation Letter Section
    elements.append(Paragraph("Statement of Purpose & Motivation Letter", section_heading))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cbd5e1"), spaceAfter=6))

    paragraphs = [p.strip() for p in motivation_letter.split("\n") if p.strip()]
    if not paragraphs:
        paragraphs = ["Statement of Purpose content pending generation."]

    for para_text in paragraphs:
        elements.append(Paragraph(para_text, letter_text_style))

    # 5. Footer & Verification Stamp
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=4))
    footer_text = (
        "<b>AUSA Advisory Engine Verification</b> — Generated automatically based on verified student "
        "academic credentials and target university admissions guidelines."
    )
    elements.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=7.5, leading=10, textColor=colors.HexColor("#64748b"))))

    # Build PDF binary
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

