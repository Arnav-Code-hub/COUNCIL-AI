# Verification — 30 October 2026

## Independent application
- Backend: 50 tests passed, including outgoing schema compatibility and rejection
  of oversized strengths, issues, limitations and reference lists.
- Ruff check and formatting check passed.
- Frontend: 4 component tests, TypeScript/Vite build and one Chrome end-to-end
  test passed. Browser acceptance covers submission, PDF download, refresh
  persistence and mobile history/layout.
- PDF sample pages were rendered and inspected during implementation.
- Independent review found no remaining Critical/Moderate defects in the offline scope.

## JanMaang boundary
- 129 API unit tests passed; mypy and Ruff passed; both import contracts kept.
- All 144 frontend tests passed using one worker, plus TypeScript and ESLint.
  A parallel run timed out on an asynchronous supervisor selector assertion under
  machine contention; the serial run passed without a test or product workaround.
- Four real PostgreSQL acceptance tests passed in a disposable container with the
  complete Alembic chain: supervision/private access; concurrent idempotency;
  PDF publication retry reusing the upstream identity; atomic rollback after
  notification inserts. Remote model calls are mocked in these tests.
- No production database was used. Disposable test containers were removed.
- No integration has been enabled, merged, pushed or deployed.

## Container acceptance
The Docker image built successfully using an optional trusted-CA BuildKit secret
for this network's TLS interception. A disposable simulation container passed
health/UI, five-reviewer completion, idempotent replay and four-page PDF download.
It ran as the non-root council user with one worker on a host-loopback-only port.
The image's Gemini source matched the current source. The build secret was absent
at runtime. Test container, volume and image tag were removed; Docker Desktop and
the build cache remain.

## Live provider acceptance
A synthetic-only smoke test used existing server-side configuration, without
sending student data or changing the production model setting. It exposed and
fixed two adapter defects: certificate trust now uses a verifying system SSL
context; structured output uses the SDK's native response_json_schema path.
Both fixes are covered by regression assertions.

On the latest resume, gemini-3.5-flash-lite completed a genuine five-reviewer
synthetic assessment and generated a PDF. A minimal gemini-3.6-flash request also
succeeded; gemini-3.8-flash still returned HTTP 504 with a 60-second deadline.
The main application's existing provider configuration was not changed.

Isolated probes exposed a separate HTTP 400: Gemini rejected the full nested
array maxima in the response schema. Removing only maxItems made the same schema
succeed. Only the outgoing generation schema is simplified; all Pydantic limits,
required fields, evidence references, output length and call bounds remain enforced.
Deprecated temperature configuration was removed.

Structural completion did not establish semantic quality. Prompt 1.0 repeatedly
classified missing measurements as contradicted/Critical. Prompt 1.1 corrected
that classification, but produced scope creep and unsupported SQL consequences.
Prompt 1.2 strengthens scope and consequence qualification. Earlier failed outputs
are retained privately as calibration history, not approved examples.

All four synthetic cases completed three runs each with prompt 1.2: 12 assessments,
60 validated reviewer outputs and 60 PDF pages. Exact case evidence, reference
bounds and PDF hashes were rechecked. Unsupported-impact and contradictory-data
cases retained the correct central classifications across all repetitions; prompt
injection was ignored and parameter binding recommended. This is structural
acceptance and developer screening, not a calibrated quality pass.

Three Moderate semantic failures remain in developer screening:
- SQL run 2 Evidence examiner labels the safety claim supported while diagnosing
  the unsafe concatenation.
- Bounded run 3 Sceptic raises a nonnumeric-input defect outside the explicit
  negative-integer claim, without a caller requiring that wider contract.
- SQL run 1 Engineer and run 3 Impact say tests were not performed, although the
  supplied evidence establishes only that tests were not supplied.

Do not silently rewrite these judgments or claim student readiness from structural
completion. Comparing a more capable model and collecting faculty decisions are
the next quality tasks; further prompt tuning alone is not proof of reliability.

Visual inspection of 41 pages across the eight first/third-run PDFs found no
clipping, overlap or unreadable references/footers. Minor pagination limitations
remain: an isolated citation or a short reference-resolution section can move to
a new page. Second-run PDFs were structurally checked but not visually inspected.

No faculty has approved any model output, and no authenticated live student/faculty
round trip has been performed. Default settings remain simulation and quality
approval false. Student enablement remains blocked on faculty calibration and
integrated authorization/delivery acceptance.

Keep COUNCIL_MODE=simulation and COUNCIL_LIVE_QUALITY_APPROVED=false until a current
model successfully completes synthetic acceptance and faculty calibration. Never
treat simulated feedback or a configuration flag as proof of accuracy.
