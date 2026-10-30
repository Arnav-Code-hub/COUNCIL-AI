"""Build a manual calibration checklist from an exported completed assessment."""

import argparse
import json
from pathlib import Path

from council.engine import validate_references
from council.schemas import REVIEWERS, Project, Report, evidence_inventory

CASES = Path(__file__).with_name("cases.json")


def review_packet(case_id: str, exported: dict) -> str:
    cases = {case["id"]: case for case in json.loads(CASES.read_text(encoding="utf-8"))}
    if case_id not in cases:
        raise ValueError("Unknown calibration case.")
    case = cases[case_id]
    expected = Project.model_validate(case["project"])
    supplied = Project.model_validate(exported["project"])
    if supplied != expected:
        raise ValueError("Exported evidence does not match the calibration case.")
    if exported.get("status") != "completed":
        raise ValueError("Calibration requires a completed assessment.")
    report = Report.model_validate(exported["report"])
    if report.simulated:
        raise ValueError(
            "Calibration requires a live report; simulated reviews are not quality evidence."
        )
    identities = [review.reviewer for review in report.reviewers]
    if sorted(identities) != sorted(REVIEWERS):
        raise ValueError("Calibration requires all five reviewers exactly once.")
    for review in report.reviewers:
        validate_references(review, evidence_inventory(expected))
    lines = [
        "# HUMAN REVIEW REQUIRED",
        "",
        f"Case: {case_id}",
        f"Purpose: {case['purpose']}",
        f"Model: {report.model} | Prompt version: {report.prompt_version}",
        "",
        "Structural validation passed. This does not establish semantic accuracy or safety.",
        "",
        "Human reviewer: __________________",
        "Review date: __________________",
        "Decision (pass / fail / needs revision): __________________",
        "",
        "## Required checks",
        "",
    ]
    lines += [f"- [ ] {question}" for question in case["review_questions"]]
    lines += ["", "## Blocking failures (each must be absent)", ""]
    lines += [f"- [ ] Absent: {failure}" for failure in case["blocking_failures"]]
    lines += [
        "",
        "## Common checks",
        "",
        "- [ ] Every material claim and strength has a relevant, accurate citation.",
        "- [ ] No invented facts, automatic grades, badges or independent execution claims.",
        "- [ ] Each shortcoming has a concrete consequence, improvement and verification step.",
        "- [ ] Missing evidence and disagreement are visible; confidence is proportional.",
        "",
        "Evidence and reasoning for the human decision: __________________",
        "",
        "This checklist never sets COUNCIL_LIVE_QUALITY_APPROVED or authorizes student deployment.",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument(
        "--report",
        required=True,
        type=Path,
        help="JSON from GET /v1/assessments/{id}; includes exact project snapshot and report.",
    )
    args = parser.parse_args()
    try:
        exported = json.loads(args.report.read_text(encoding="utf-8"))
        print(review_packet(args.case, exported))
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
