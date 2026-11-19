"""
Shared styles, palette, typography, and helper builders for the study guide.
"""
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, KeepTogether
from reportlab.lib.units import inch

# Color Palette
PRIMARY = colors.HexColor("#0F172A")      # Slate 900
PRIMARY_LIGHT = colors.HexColor("#1E293B")# Slate 800
ACCENT = colors.HexColor("#1D4ED8")       # Blue 700
ACCENT_LIGHT = colors.HexColor("#EFF6FF") # Blue 50
TEXT_MAIN = colors.HexColor("#1E293B")    # Slate 800
TEXT_MUTED = colors.HexColor("#64748B")   # Slate 500
BORDER_COLOR = colors.HexColor("#CBD5E1") # Slate 300
ROW_BG_ALT = colors.HexColor("#F8FAFC")   # Slate 50
CODE_BG = colors.HexColor("#F1F5F9")      # Slate 100
CALLOUT_BG = colors.HexColor("#F8FAFC")
CALLOUT_BORDER = colors.HexColor("#3B82F6") # Blue 500
SUCCESS_COLOR = colors.HexColor("#15803D") # Green 700
WARNING_COLOR = colors.HexColor("#B45309") # Amber 700

styles = getSampleStyleSheet()

# Custom Paragraph Styles
CoverTitle = ParagraphStyle(
    "CoverTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=26,
    leading=32,
    textColor=PRIMARY,
    alignment=1, # Center
    spaceAfter=12,
)

CoverSubtitle = ParagraphStyle(
    "CoverSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=14,
    leading=18,
    textColor=ACCENT,
    alignment=1,
    spaceAfter=24,
)

CoverMeta = ParagraphStyle(
    "CoverMeta",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=14,
    textColor=TEXT_MUTED,
    alignment=1,
)

H1 = ParagraphStyle(
    "SectionH1",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=20,
    textColor=PRIMARY,
    spaceBefore=14,
    spaceAfter=6,
    keepWithNext=True,
)

H2 = ParagraphStyle(
    "SectionH2",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=16,
    textColor=ACCENT,
    spaceBefore=10,
    spaceAfter=4,
    keepWithNext=True,
)

H3 = ParagraphStyle(
    "SectionH3",
    parent=styles["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=13,
    textColor=PRIMARY_LIGHT,
    spaceBefore=8,
    spaceAfter=3,
    keepWithNext=True,
)

Body = ParagraphStyle(
    "DocBody",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=12,
    textColor=TEXT_MAIN,
    spaceAfter=5,
)

BodyBold = ParagraphStyle(
    "DocBodyBold",
    parent=Body,
    fontName="Helvetica-Bold",
)

BodySmall = ParagraphStyle(
    "DocBodySmall",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7.5,
    leading=10.5,
    textColor=TEXT_MUTED,
)

BulletText = ParagraphStyle(
    "DocBullet",
    parent=Body,
    leftIndent=14,
    firstLineIndent=-10,
    spaceAfter=3,
)

CodeText = ParagraphStyle(
    "DocCode",
    parent=styles["Normal"],
    fontName="Courier",
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor("#0F172A"),
)

TableHeader = ParagraphStyle(
    "DocTableHeader",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10.5,
    textColor=colors.white,
    alignment=0,
)

TableCell = ParagraphStyle(
    "DocTableCell",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7.5,
    leading=10,
    textColor=TEXT_MAIN,
)

TableCellBold = ParagraphStyle(
    "DocTableCellBold",
    parent=TableCell,
    fontName="Helvetica-Bold",
)

TableCellCode = ParagraphStyle(
    "DocTableCellCode",
    parent=TableCell,
    fontName="Courier",
    fontSize=7,
    leading=9,
)

def make_callout(title: str, text: str, kind: str = "info"):
    """Creates a styled callout box with a prominent colored left border."""
    border_col = CALLOUT_BORDER
    bg_col = CALLOUT_BG
    if kind == "success":
        border_col = SUCCESS_COLOR
        bg_col = colors.HexColor("#F0FDF4")
    elif kind == "warning":
        border_col = WARNING_COLOR
        bg_col = colors.HexColor("#FFFBEB")

    title_p = Paragraph(f"<b>{title}</b>", ParagraphStyle(
        "CalloutTitle", parent=BodyBold, textColor=border_col, spaceAfter=2
    ))
    text_p = Paragraph(text, ParagraphStyle(
        "CalloutText", parent=Body, spaceAfter=0
    ))
    t = Table([[title_p], [text_p]], colWidths=[520])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_col),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("LINELEFT", (0, 0), (0, -1), 3.0, border_col),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t

def make_code_box(code_str: str):
    """Creates a monospace code block in a light slate box."""
    p = Paragraph(code_str.replace("\n", "<br/>").replace(" ", "&nbsp;"), CodeText)
    t = Table([[p]], colWidths=[520])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t
