# Council service contract v1
All private endpoints require the server-only `X-Council-Key` when configured.
The entire service is a single trusted workspace. It does not accept end-user
identity assertions or enforce JanMaang roles; JanMaang must authorize every
request and every PDF retrieval. There are no cross-repository source imports.

- `POST /v1/assessments`, `Idempotency-Key`: project evidence JSON. Returns 202
  with `{id,status}`. The same key/evidence returns the original ID; the same key
  with changed evidence returns 409. Model calls run after request acceptance.
- `GET /v1/assessments/{uuid}`: immutable project snapshot and hash, creation
  timestamp, status, completed reviewer count, report or null, sanitized error.
- `POST /v1/assessments/{uuid}/retry`, `Idempotency-Key`: retry incomplete
  assessments only. Persist a fresh key for each explicit retry action and reuse
  it on transport retries. Replaying a key never starts a second model run,
  including after another failure or a process restart. Cross-assessment key
  reuse returns 409.
- `GET /v1/assessments/{uuid}/pdf`: completed private PDF; 409 while incomplete,
  503 if a completed artifact is missing from storage.
- `GET /v1/assessments`: most recent 100 local-workspace entries. Do not proxy this
  unscoped endpoint to JanMaang end users.
- `GET /health`: public liveness, mode, contract version.

Status: queued -> running -> completed OR incomplete. No score or grade fields.
Version 1.0 report contains simulation flag, model/prompt versions, five reviewer
reports, consolidated priorities, disagreements and limitations. Each strength and
issue cites evidence IDs and inclusive line ranges; the service validates every
reference. Deduplication combines equal normalized issue titles and retains all
reviewer variants; it does not claim to detect arbitrary semantic equivalence.
The PDF includes evidence names, hashes and line counts. Resolve citations against
the immutable evidence snapshot in the workspace; full sources are not reproduced
in PDFs, preventing blank-line-heavy input from inflating report generation work.

Project fields: title, research_question, findings, methods, results, limitations,
files (name, content). See `/openapi.json` for exact versioned schemas. Methods,
results and limitations can be empty; the council must report missing evidence
without inventing it. Display outputs as escaped text, never executable HTML.

JanMaang owns supervisor assignment and a durable request/publication record.
Require institute assignment before enqueueing; snapshot the assigned supervisor.
Use the durable record ID for the council idempotency key. After completion,
record availability for the team and supervisor before marking publication
successful. Retry delivery/polling using the original council ID, not a new
assessment. JanMaang must not expose service credentials or unscoped council
history. Human faculty reviews and scores remain independent.
