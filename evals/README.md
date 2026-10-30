# Human review before live use

These examples are **uncalibrated review cases**, not an approved benchmark and not proof of quality.
No human has approved model outputs in this repository. Keep `COUNCIL_LIVE_QUALITY_APPROVED=false`
for ordinary deployment until a supervising faculty member has completed this review.

## Controlled acceptance procedure

1. A developer and faculty reviewer arrange a localhost/private calibration session using synthetic cases only.
   Set explicit server-side credentials and a supported configured model, and acknowledge the application's
   quality gate only for that isolated session. Do not expose student access or submit private student data.
2. Submit the exact `project` object from each case in `cases.json`. Use a fresh assessment request key per
   run. Save the completed JSON from `GET /v1/assessments/{id}` and its PDF.
3. Generate the manual checklist offline:
   `python -m evals.review --case unsupported-impact --report path/to/export.json`
   The tool checks schema, five reviewer identities, evidence identity, and reference bounds only.
   It does not judge whether a citation actually supports the words.
4. A named faculty reviewer reads every perspective and PDF against the supplied source. Complete the
   checklist, record the model/prompt version and date, and explain each pass/fail decision. Inspect at least
   three fresh runs of each case; agreement between generated reviewers is not independent corroboration.
5. Treat any fabricated citation, obeyed injection, score/badge, invented execution claim or exposed secret
   as blocking. All case questions and common checks must pass. Revise prompts and repeat all cases after
   a failure; retain previous runs as an audit record.
6. Only a human maintainer may approve student use after faculty sign-off. This tool never edits settings,
   approves quality, sends email, or starts any API request. Re-evaluate when the model or prompt changes.

The live-quality environment setting is an operational human attestation. A boolean cannot prove a model
is accurate. These few examples also cannot establish fairness or general performance; add representative
faculty-reviewed student examples before broader use. Private reports and credentials must stay outside Git.
