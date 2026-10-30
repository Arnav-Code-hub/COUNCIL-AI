import pytest
from fastapi.testclient import TestClient
from test_contracts import project

from council.config import Settings
from council.engine import SimulatedReviewer, assess, consolidate
from council.main import create_app
from council.schemas import REVIEWERS, EvidenceRef, Issue, ReviewerReport


def test_five_reviewer_report_is_repeatable_and_honest():
    a = assess(project(), SimulatedReviewer())
    b = assess(project(), SimulatedReviewer())
    assert a == b
    assert list(r.reviewer for r in a.reviewers) == list(REVIEWERS)
    assert a.simulated
    assert all(r.strengths and r.issues for r in a.reviewers)
    assert all(i.claim_status == "not_verifiable" for r in a.reviewers for i in r.issues)


def test_bad_evidence_references_rejected():
    class Bad(SimulatedReviewer):
        def review(self, reviewer, inventory):
            r = super().review(reviewer, inventory)
            r.issues[0].evidence = [EvidenceRef(evidence_id="E99", start_line=1, end_line=2)]
            return r

    with pytest.raises(ValueError, match="reference"):
        assess(project(), Bad())


def test_failure_does_not_complete():
    class Failed:
        def review(self, *args):
            raise TimeoutError("provider unavailable")

    with pytest.raises(TimeoutError):
        assess(project(), Failed())


def test_consolidation_keeps_disagreements_and_attribution():
    issue = dict(
        title="Claim needs evidence",
        severity="Moderate",
        claim_status="supported",
        detail="A finding.",
        consequence="Unsupported conclusion.",
        improvement="Add baseline.",
        verification="Repeat measurement.",
        evidence=[dict(evidence_id="E01", start_line=1, end_line=1)],
    )
    a = ReviewerReport(
        reviewer="evidence", strengths=[], issues=[Issue(**issue)], limitations=["Limited input."]
    )
    b = a.model_copy(deep=True, update={"reviewer": "engineer"})
    b.issues[0].claim_status = "contradicted"
    out = consolidate([a, b])
    assert len(out) == 1
    assert out[0].reviewers == ["evidence", "engineer"]
    assert out[0].disagreement


def test_api_persistence_idempotency_and_pdf(tmp_path):
    settings = Settings(data_dir=tmp_path)
    with TestClient(create_app(settings)) as c:
        body = project().model_dump()
        a = c.post("/v1/assessments", json=body, headers={"Idempotency-Key": "request-1"})
        assert a.status_code == 202, a.text
        ident = a.json()["id"]
        b = c.post("/v1/assessments", json=body, headers={"Idempotency-Key": "request-1"})
        assert b.json()["id"] == ident
        body["results"] = "Different result"
        assert (
            c.post(
                "/v1/assessments", json=body, headers={"Idempotency-Key": "request-1"}
            ).status_code
            == 409
        )
        result = c.get(f"/v1/assessments/{ident}").json()
        assert result["status"] == "completed"
        assert result["completed_reviewers"] == 5
        pdf = c.get(f"/v1/assessments/{ident}/pdf")
        assert pdf.content.startswith(b"%PDF-")
    with TestClient(create_app(settings)) as c:
        assert c.get(f"/v1/assessments/{ident}").json()["status"] == "completed"
        assert len(c.get("/v1/assessments").json()) == 1


def test_service_auth_and_browser_origin(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path, service_key="a" * 40))) as c:
        assert c.get("/v1/assessments").status_code == 401
        assert c.get("/v1/assessments", headers={"X-Council-Key": "wrong"}).status_code == 401
        assert c.get("/v1/assessments", headers={"X-Council-Key": "a" * 40}).status_code == 200
    with TestClient(create_app(Settings(data_dir=tmp_path))) as c:
        assert (
            c.post(
                "/v1/assessments",
                json=project().model_dump(),
                headers={"Origin": "https://evil.example", "Idempotency-Key": "evil"},
            ).status_code
            == 403
        )


def test_restart_marks_pending_incomplete(tmp_path):
    app = create_app(Settings(data_dir=tmp_path))
    row, _ = app.state.store.create("restart", project())
    with TestClient(create_app(Settings(data_dir=tmp_path))) as c:
        assert c.get(f"/v1/assessments/{row['id']}").json()["status"] == "incomplete"
