# Verification — 30 October 2026

## Independent application
- Backend: 45 tests passed.
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

## Live provider limitations
A synthetic-only smoke test used existing server-side configuration, without
sending student data or changing the production model setting. It exposed and
fixed two adapter defects: certificate trust now uses a verifying system SSL
context; structured output uses the SDK's native response_json_schema path.
Both fixes are covered by regression assertions.

The previously configured gemini-2.5-flash was rejected as retired for this account.
The provider recommended gemini-3.8-flash and lists it as available, but minimal,
JSON and council-schema probes returned deadline errors. No complete live council
assessment was produced. This does not establish model quality or approval.

Keep COUNCIL_MODE=simulation and COUNCIL_LIVE_QUALITY_APPROVED=false until a current
model successfully completes synthetic acceptance and faculty calibration. Never
treat simulated feedback or a configuration flag as proof of accuracy.
