"""Versioned, bounded evidence and reviewer contracts."""

import hashlib
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

REVIEWERS = {
    "evidence": "Evidence examiner",
    "engineer": "Engineer",
    "sceptic": "Sceptic",
    "impact": "Impact reviewer",
    "delivery": "Delivery reviewer",
}
Reviewer = Literal["evidence", "engineer", "sceptic", "impact", "delivery"]
Severity = Literal["Critical", "Moderate", "Nitpick"]
ClaimStatus = Literal["supported", "contradicted", "not_verifiable"]
Text = Annotated[str, Field(min_length=1, max_length=4000)]
EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".dart",
    ".java",
    ".go",
    ".rs",
    ".html",
    ".css",
    ".sql",
    ".json",
    ".yaml",
    ".yml",
    ".c",
    ".cpp",
    ".h",
}


def valid_text(value: str) -> str:
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError("Text must be valid UTF-8.") from exc
    if any(ord(c) < 32 and c not in "\n\r\t" for c in value):
        raise ValueError("Control characters are not accepted.")
    return value.replace("\r\n", "\n").replace("\r", "\n")


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class EvidenceFile(Contract):
    name: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1, max_length=50000)

    @field_validator("name")
    @classmethod
    def filename(cls, value: str) -> str:
        from pathlib import PurePosixPath

        if (
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_. -]*", value)
            or ".." in value
            or value.endswith((" ", "."))
            or PurePosixPath(value).suffix.lower() not in EXTENSIONS
        ):
            raise ValueError("Use a plain filename with an accepted text/source extension.")
        return value

    @field_validator("content")
    @classmethod
    def content_text(cls, value: str) -> str:
        value = valid_text(value)
        if not value.strip():
            raise ValueError("Evidence files must not be empty.")
        return value


class Project(Contract):
    title: str = Field(min_length=1, max_length=200)
    research_question: str = Field(min_length=1, max_length=10000)
    findings: str = Field(min_length=1, max_length=20000)
    methods: str = Field(default="", max_length=20000)
    results: str = Field(default="", max_length=20000)
    limitations: str = Field(default="", max_length=10000)
    files: list[EvidenceFile] = Field(default_factory=list, max_length=20)

    @field_validator("title", "research_question", "findings", "methods", "results", "limitations")
    @classmethod
    def text(cls, value: str) -> str:
        return valid_text(value).strip()

    @model_validator(mode="after")
    def bounds(self):
        if not self.title or not self.research_question or not self.findings:
            raise ValueError("Title, research question and findings are required.")
        names = [f.name.casefold() for f in self.files]
        if len(names) != len(set(names)):
            raise ValueError("Evidence filenames must be unique, ignoring case.")
        fields = [
            self.title,
            self.research_question,
            self.findings,
            self.methods,
            self.results,
            self.limitations,
        ]
        if sum(len(s) for s in fields) + sum(len(f.content) for f in self.files) > 200000:
            raise ValueError("Total evidence exceeds 200,000 characters.")
        return self


class Evidence(Contract):
    id: str
    name: str
    sha256: str
    lines: list[str]


def evidence_inventory(project: Project) -> list[Evidence]:
    parts = [
        (key, getattr(project, key))
        for key in ("research_question", "findings", "methods", "results", "limitations")
    ]
    parts += [(f.name, f.content) for f in project.files]
    return [
        Evidence(
            id=f"E{i:02}",
            name=name,
            sha256=hashlib.sha256(content.encode()).hexdigest(),
            lines=content.splitlines() or [""],
        )
        for i, (name, content) in enumerate(parts, 1)
    ]


class EvidenceRef(Contract):
    evidence_id: str = Field(pattern=r"^E[0-9]{2}$")
    start_line: int = Field(ge=1, strict=True)
    end_line: int = Field(ge=1, strict=True)


class Issue(Contract):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    severity: Severity
    claim_status: ClaimStatus
    detail: Text
    consequence: Text
    improvement: Text
    verification: Text
    evidence: list[EvidenceRef] = Field(min_length=1, max_length=10)


class Strength(Contract):
    detail: Text
    evidence: list[EvidenceRef] = Field(min_length=1, max_length=10)


class ReviewerReport(Contract):
    reviewer: Reviewer
    strengths: list[Strength] = Field(max_length=10)
    issues: list[Issue] = Field(max_length=15)
    limitations: list[Text] = Field(min_length=1, max_length=10)


class ConsolidatedIssue(Contract):
    title: str
    severity: Severity
    reviewers: list[Reviewer]
    issues: list[Issue]
    disagreement: bool


class Report(Contract):
    version: Literal["1.0"] = "1.0"
    simulated: bool
    model: str
    prompt_version: str
    summary: str
    reviewers: list[ReviewerReport]
    priorities: list[ConsolidatedIssue]
    limitations: list[str]
