from io import BytesIO

from pypdf import PdfReader
from test_contracts import project

from council.engine import SimulatedReviewer, assess
from council.pdf import make_pdf


def test_pdf_escapes_markup_and_keeps_references_and_unicode():
    p = project()
    report = assess(p, SimulatedReviewer())
    report.reviewers[0].issues[0].detail = '<img src="https://evil.test/secret"/> café Δ →'
    result = make_pdf("test", "2026-10-30T06:00:00Z", p, report)
    reader = PdfReader(BytesIO(result))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "SIMULATION" in text
    assert 'src="https://evil.test/secret"' in text
    assert "café" in text and "Δ" in text
    assert "E02:L1-1" in text
    assert "Page 1" in text


def test_long_report_paginates_without_truncation():
    p = project(
        files=[
            {
                "name": "x" * 120 + ".txt",
                "content": "A long finding and its evidence. " * 1400 + " END-OF-EVIDENCE",
            }
        ]
    )
    report = assess(p, SimulatedReviewer())
    for review in report.reviewers:
        review.issues[0].detail = (
            "A detailed critique of the supplied evidence. " * 75 + " END-OF-REPORT"
        )
    result = make_pdf("long", "2026-10-30T06:00:00Z", p, report)
    reader = PdfReader(BytesIO(result))
    assert len(reader.pages) > 5
    assert "END-OF-REPORT" in "\n".join(page.extract_text() for page in reader.pages)
    assert all("SIMULATION" in page.extract_text() for page in reader.pages)
