"""Render escaped text only; never load resources from student content."""

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate

from council.schemas import REVIEWERS, Project, Report, evidence_inventory

FONT = Path(__file__).parent / "fonts" / "DejaVuSans.ttf"


def make_pdf(identity: str, created_at: str, project: Project, report: Report) -> bytes:
    if "Council" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("Council", str(FONT)))
    styles = {
        "body": ParagraphStyle(
            "body", fontName="Council", fontSize=9, leading=14, spaceAfter=7, wordWrap="CJK"
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName="Council",
            fontSize=25,
            leading=31,
            spaceAfter=16,
            textColor=colors.HexColor("#173e39"),
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Council",
            fontSize=14,
            leading=20,
            spaceBefore=16,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "small": ParagraphStyle(
            "small",
            fontName="Council",
            fontSize=8,
            leading=12,
            spaceAfter=6,
            textColor=colors.HexColor("#485551"),
        ),
    }
    story = []
    font = pdfmetrics.getFont("Council")

    def text(value):
        # Unsupported characters are printed as explicit Unicode code points, never missing glyph boxes.
        value = "".join(
            c if ord(c) in font.face.charToGlyph or c in "\n\t" else f"[U+{ord(c):04X}]"
            for c in str(value)
        )
        return escape(value).replace("\n", "<br/>")

    def add(value, style="body"):
        story.append(Paragraph(text(value), styles[style]))

    def refs(items):
        return "; ".join(f"{r.evidence_id}:L{r.start_line}-{r.end_line}" for r in items)

    add("AI COUNCIL / ADVISORY REPORT", "small")
    add(project.title, "h1")
    add(
        f"Report {identity} | Version {report.version}\nCreated {created_at} (UTC)\nModel: {report.model} | Prompts: {report.prompt_version}",
        "small",
    )
    add("Executive assessment", "h2")
    add(report.summary)
    for limit in report.limitations:
        add(limit, "small")
    add("Evidence inventory", "h2")
    for e in evidence_inventory(project):
        add(f"{e.id} | {e.name} | {len(e.lines)} lines\nSHA-256: {e.sha256}", "small")
    add("Prioritized improvements and disagreements", "h2")
    if not report.priorities:
        add("No shortcomings were reported. This is not proof of correctness.")
    for i, group in enumerate(report.priorities, 1):
        add(f"{i}. {group.severity}: {group.title}", "h2")
        add("Reviewers: " + ", ".join(REVIEWERS[r] for r in group.reviewers), "small")
        if group.disagreement:
            add("DISAGREEMENT: reviewer judgments differ. See each perspective below.")
        for issue in group.issues:
            add(f"Improve: {issue.improvement}\nVerify: {issue.verification}")
    for review in report.reviewers:
        add(REVIEWERS[review.reviewer], "h2")
        add("Strengths", "h2")
        for strength in review.strengths:
            add(strength.detail)
            add(refs(strength.evidence), "small")
        if not review.strengths:
            add("No supported strengths identified from supplied evidence.")
        add("Detailed critique", "h2")
        for issue in review.issues:
            add(f"{issue.severity} / {issue.claim_status.replace('_', ' ')}: {issue.title}", "h2")
            add(issue.detail)
            add("Consequence: " + issue.consequence)
            add("Improvement: " + issue.improvement)
            add("Verification: " + issue.verification)
            add(refs(issue.evidence), "small")
        for limit in review.limitations:
            add("Limitation: " + limit, "small")
    add("Resolving evidence references", "h2")
    add(
        "References identify evidence entries in the inventory and inclusive source line ranges. Read them against the immutable evidence snapshot in the workspace. Source files are not reproduced in this report.",
        "small",
    )
    buf = BytesIO()

    def page(canvas, doc):
        canvas.setFont("Council", 8)
        canvas.setFillColor(colors.HexColor("#485551"))
        canvas.drawString(
            42,
            27,
            "AI Council | Advisory | "
            + ("SIMULATION" if report.simulated else "Faculty judgment required"),
        )
        canvas.drawRightString(A4[0] - 42, 27, f"Page {doc.page}")
        if report.simulated:
            canvas.saveState()
            canvas.setFillColor(colors.HexColor("#eeeeee"))
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(40)
            canvas.setFont("Council", 52)
            canvas.drawCentredString(0, 0, "SIMULATION")
            canvas.restoreState()

    SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=40,
        bottomMargin=48,
        title=project.title,
        author="AI Council",
    ).build(story, onFirstPage=page, onLaterPages=page)
    return buf.getvalue()
