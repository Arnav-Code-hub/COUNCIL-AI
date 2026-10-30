from io import BytesIO

from pypdf import PdfReader
from test_contracts import project

from council.engine import SimulatedReviewer, assess
from council.pdf import make_pdf


def test_blank_source_lines_do_not_amplify_report_pages():
    p = project(files=[{"name": "notes.txt", "content": "\n" * 4999 + "x"}])
    pdf = make_pdf("bounded", "2026-10-30", p, assess(p, SimulatedReviewer()))
    assert len(PdfReader(BytesIO(pdf)).pages) < 20
