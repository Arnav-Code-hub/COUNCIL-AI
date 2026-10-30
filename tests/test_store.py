import sqlite3

import pytest
from fastapi.testclient import TestClient
from test_contracts import project

from council.config import Settings
from council.main import create_app
from council.store import Store


def test_connections_close_after_transaction(tmp_path):
    store = Store(tmp_path)
    with store.connect() as connection:
        connection.execute("SELECT 1")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")


def test_retry_respects_capacity_and_returns_429(tmp_path):
    application = create_app(Settings(data_dir=tmp_path))
    with TestClient(application) as client:
        store = application.state.store
        rows = []
        for n in range(11):
            row, _ = store.create(str(n), project())
            store.update(row["id"], "incomplete")
            rows.append(row)
        for row in rows[:10]:
            assert store.retry(row["id"], "retry-" + row["id"])
        assert (
            client.post(
                "/v1/assessments/" + rows[10]["id"] + "/retry", headers={"Idempotency-Key": "full"}
            ).status_code
            == 429
        )
        assert store.get(rows[10]["id"])["status"] == "incomplete"


def test_retry_request_is_durable_and_does_not_regenerate_after_failure(tmp_path):
    from council.engine import SimulatedReviewer

    class Failing(SimulatedReviewer):
        calls = 0

        def review(self, reviewer, inventory):
            self.calls += 1
            raise TimeoutError("failure")

    provider = Failing()
    settings = Settings(data_dir=tmp_path)
    with TestClient(create_app(settings, provider)) as client:
        row = client.post(
            "/v1/assessments", json=project().model_dump(), headers={"Idempotency-Key": "create"}
        ).json()
        url = "/v1/assessments/" + row["id"] + "/retry"
        assert client.post(url, headers={"Idempotency-Key": "retry-once"}).status_code == 202
        assert provider.calls == 2
        assert client.post(url, headers={"Idempotency-Key": "retry-once"}).status_code == 202
        assert provider.calls == 2
    with TestClient(create_app(settings, provider)) as client:
        assert client.post(url, headers={"Idempotency-Key": "retry-once"}).status_code == 202
        assert provider.calls == 2
        other = client.post(
            "/v1/assessments", json=project().model_dump(), headers={"Idempotency-Key": "other"}
        ).json()
        assert (
            client.post(
                "/v1/assessments/" + other["id"] + "/retry",
                headers={"Idempotency-Key": "retry-once"},
            ).status_code
            == 409
        )
