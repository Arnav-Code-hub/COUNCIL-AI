import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from test_contracts import project

from council.config import Settings
from council.engine import SimulatedReviewer, assess
from council.main import create_app
from council.schemas import EvidenceRef


def test_external_host_cannot_read_local_workspace(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        assert (
            client.get("/v1/assessments", headers={"Host": "attacker.example"}).status_code == 400
        )


def test_body_limit_and_failed_retry(tmp_path):
    class Failing(SimulatedReviewer):
        def review(self, reviewer, inventory):
            raise TimeoutError("private details must not reach client")

    with TestClient(create_app(Settings(data_dir=tmp_path), provider=Failing())) as client:
        assert client.post("/v1/assessments", content=b"x" * 1000001).status_code == 413
        result = client.post(
            "/v1/assessments", json=project().model_dump(), headers={"Idempotency-Key": "fail"}
        )
        ident = result.json()["id"]
        row = client.get("/v1/assessments/" + ident).json()
        assert row["status"] == "incomplete" and row["report"] is None
        assert "private details" not in row["error"]
        assert client.get("/v1/assessments/" + ident + "/pdf").status_code == 409
        assert (
            client.post(
                "/v1/assessments/" + ident + "/retry", headers={"Idempotency-Key": "retry"}
            ).status_code
            == 202
        )


def test_live_mode_requires_explicit_approval_and_service_auth(tmp_path):
    with pytest.raises(ValidationError):
        Settings(data_dir=tmp_path, mode="gemini", gemini_key="unused", gemini_model="unused")


@pytest.mark.parametrize("start,end", [(2, 1), (1, 999)])
def test_out_of_range_lines_rejected(start, end):
    class Bad(SimulatedReviewer):
        def review(self, reviewer, inventory):
            r = super().review(reviewer, inventory)
            r.issues[0].evidence = [EvidenceRef(evidence_id="E01", start_line=start, end_line=end)]
            return r

    with pytest.raises(ValueError, match="reference"):
        assess(project(), Bad())
