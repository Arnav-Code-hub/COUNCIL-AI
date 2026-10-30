"""Single-instance SQLite store. Evidence snapshots are immutable."""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4


class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "council.sqlite3"
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS assessments (
                    id TEXT PRIMARY KEY, request_key TEXT NOT NULL UNIQUE,
                    snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
                    created_at TEXT NOT NULL, status TEXT NOT NULL,
                    completed_reviewers INTEGER NOT NULL DEFAULT 0,
                    report TEXT, error TEXT);
                CREATE TABLE IF NOT EXISTS retry_requests (
                    request_key TEXT PRIMARY KEY,
                    assessment_id TEXT NOT NULL REFERENCES assessments(id));
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            with db:
                yield db
        finally:
            db.close()

    def recover(self):
        with self.connect() as db:
            db.execute(
                "UPDATE assessments SET status='incomplete', error=? WHERE status IN ('queued','running')",
                ("Process stopped before completion. Retry this assessment explicitly.",),
            )

    def create(self, key, project):
        payload = project.model_dump_json()
        digest = hashlib.sha256(payload.encode()).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT a.id,s.sha256 FROM assessments a JOIN snapshots s ON s.id=a.snapshot_id WHERE request_key=?",
                (key,),
            ).fetchone()
            if existing:
                if existing["sha256"] != digest:
                    raise ValueError("Idempotency key already belongs to different evidence.")
                return self.get(existing["id"]), False
            if (
                db.execute(
                    "SELECT count(*) FROM assessments WHERE status IN ('queued','running')"
                ).fetchone()[0]
                >= 10
            ):
                raise OverflowError("Assessment queue is full; try again later.")
            ident, snapshot = str(uuid4()), str(uuid4())
            db.execute("INSERT INTO snapshots VALUES (?,?,?)", (snapshot, payload, digest))
            db.execute(
                "INSERT INTO assessments(id,request_key,snapshot_id,created_at,status) VALUES (?,?,?,?,?)",
                (ident, key, snapshot, datetime.now(timezone.utc).isoformat(), "queued"),
            )
        return self.get(ident), True

    def get(self, ident):
        with self.connect() as db:
            row = db.execute(
                "SELECT a.*,s.payload,s.sha256 FROM assessments a JOIN snapshots s ON s.id=a.snapshot_id WHERE a.id=?",
                (str(ident),),
            ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["project"] = json.loads(result.pop("payload"))
        result["report"] = json.loads(result["report"]) if result["report"] else None
        result.pop("request_key")
        return result

    def list(self):
        with self.connect() as db:
            rows = db.execute(
                "SELECT a.id,a.created_at,a.status,a.completed_reviewers,a.error,s.payload FROM assessments a JOIN snapshots s ON s.id=a.snapshot_id ORDER BY a.created_at DESC LIMIT 100"
            ).fetchall()
        return [
            dict(
                id=r["id"],
                title=json.loads(r["payload"])["title"],
                created_at=r["created_at"],
                status=r["status"],
                completed_reviewers=r["completed_reviewers"],
                error=r["error"],
            )
            for r in rows
        ]

    def update(self, ident, status, completed=0, report=None, error=None):
        with self.connect() as db:
            db.execute(
                "UPDATE assessments SET status=?,completed_reviewers=?,report=?,error=? WHERE id=?",
                (
                    status,
                    completed,
                    report.model_dump_json() if report else None,
                    error,
                    str(ident),
                ),
            )

    def retry(self, ident, key):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute(
                "SELECT assessment_id FROM retry_requests WHERE request_key=?", (key,)
            ).fetchone()
            if prior:
                if prior["assessment_id"] != str(ident):
                    raise ValueError("Retry key already belongs to a different assessment.")
                return False
            row = db.execute("SELECT status FROM assessments WHERE id=?", (str(ident),)).fetchone()
            if not row or row["status"] != "incomplete":
                raise ValueError("Only incomplete assessments can be retried.")
            if (
                db.execute(
                    "SELECT count(*) FROM assessments WHERE status IN ('queued','running')"
                ).fetchone()[0]
                >= 10
            ):
                raise OverflowError("Assessment queue is full; try again later.")
            db.execute("INSERT INTO retry_requests VALUES (?, ?)", (key, str(ident)))
            db.execute(
                "UPDATE assessments SET status='queued',completed_reviewers=0,error=NULL WHERE id=? AND status='incomplete'",
                (str(ident),),
            )
        return True
