"""No tools, code execution, or repository fetching."""

import re
from typing import Protocol

from council.schemas import (
    REVIEWERS,
    ConsolidatedIssue,
    Evidence,
    EvidenceRef,
    Issue,
    Project,
    Report,
    ReviewerReport,
    Strength,
    evidence_inventory,
)


class ReviewerProvider(Protocol):
    simulated: bool
    model: str

    def review(self, reviewer: str, inventory: list[Evidence]) -> ReviewerReport: ...


class SimulatedReviewer:
    simulated = True
    model = "deterministic-fixture-v1"

    def review(self, reviewer, inventory):
        sections = {s.name: s for s in inventory}
        focuses = {
            "evidence": (
                "methods",
                "Establish a reproducible baseline",
                "Supply methods, raw observations, a baseline and uncertainty.",
                "Reproduce the comparison against the same baseline.",
            ),
            "engineer": (
                "findings",
                "Validate implementation claims",
                "Supply relevant source, architecture decisions and failure tests.",
                "Trace one claimed behaviour from input to persisted output.",
            ),
            "sceptic": (
                "findings",
                "Establish security and privacy boundaries",
                "Document trust boundaries and test unauthorized and malformed requests.",
                "Demonstrate denied access and safe handling of invalid inputs.",
            ),
            "impact": (
                "results",
                "Demonstrate benefit to intended users",
                "Supply outcome measurements and accessibility/user feedback evidence.",
                "Compare the intended outcome with observed pilot measurements.",
            ),
            "delivery": (
                "limitations",
                "Provide a reproducible validation package",
                "Supply setup instructions, test results and known limitations.",
                "Have another person reproduce the documented test and demo.",
            ),
        }
        field, title, improvement, verification = focuses[reviewer]
        target = sections[field]
        ref = EvidenceRef(evidence_id=target.id, start_line=1, end_line=1)
        return ReviewerReport(
            reviewer=reviewer,
            strengths=[
                Strength(
                    detail="A project question and findings have been supplied. This is a structural observation, not verification of their correctness.",
                    evidence=[
                        EvidenceRef(
                            evidence_id=sections["research_question"].id, start_line=1, end_line=1
                        )
                    ],
                )
            ],
            issues=[
                Issue(
                    title=title,
                    severity="Moderate",
                    claim_status="not_verifiable",
                    detail="SIMULATION: this fixture demonstrates the review workflow. It does not interpret or substantiate the supplied claims.",
                    consequence="Treating this placeholder as a real evaluation could give false confidence.",
                    improvement=improvement,
                    verification=verification,
                    evidence=[ref],
                )
            ],
            limitations=[
                "Simulated reviewer; no semantic assessment or external verification was performed."
            ],
        )


def consolidate(reports):
    groups = {}
    order = {"Critical": 0, "Moderate": 1, "Nitpick": 2}
    for report in reports:
        for issue in report.issues:
            key = re.sub(r"\W+", " ", issue.title.casefold()).strip()
            if key not in groups:
                groups[key] = ConsolidatedIssue(
                    title=issue.title,
                    severity=issue.severity,
                    reviewers=[],
                    issues=[],
                    disagreement=False,
                )
            group = groups[key]
            if report.reviewer not in group.reviewers:
                group.reviewers.append(report.reviewer)
            group.issues.append(issue)
            group.severity = min((group.severity, issue.severity), key=order.get)
            group.disagreement = len({(i.claim_status, i.severity) for i in group.issues}) > 1
    return sorted(groups.values(), key=lambda g: order[g.severity])


def validate_references(report, inventory):
    sizes = {e.id: len(e.lines) for e in inventory}
    for item in [*report.issues, *report.strengths]:
        for ref in item.evidence:
            if (
                ref.evidence_id not in sizes
                or not 1 <= ref.start_line <= ref.end_line <= sizes[ref.evidence_id]
            ):
                raise ValueError("Invalid evidence reference in reviewer output.")


def assess(project: Project, provider: ReviewerProvider, progress=None) -> Report:
    inventory = evidence_inventory(project)
    reviews = []
    for reviewer in REVIEWERS:
        result = ReviewerReport.model_validate(provider.review(reviewer, inventory).model_dump())
        if result.reviewer != reviewer:
            raise ValueError("Reviewer identity mismatch.")
        validate_references(result, inventory)
        reviews.append(result)
        if progress:
            progress(len(reviews))
    return Report(
        simulated=provider.simulated,
        model=provider.model,
        prompt_version="1.2",
        summary=(
            "SIMULATION: workflow demonstration; not an evaluation of this project."
            if provider.simulated
            else "Advisory review of supplied evidence. Read all five perspectives and their disagreements; faculty retain judgment."
        ),
        reviewers=reviews,
        priorities=consolidate(reviews),
        limitations=[
            "Only supplied evidence was inspected. Source code was not executed.",
            "No independent factual verification was performed.",
            "Five reviewer personalities can share the same model's blind spots.",
        ],
    )
