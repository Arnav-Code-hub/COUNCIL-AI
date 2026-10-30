# Implementation ledger
Current checkpoint, 30 October 2026: resumed by the user. The COUNCIL-AI
repository is pushed; its initial GitHub CI passed. Standalone backend: 50 tests
pass. Genuine five-reviewer synthetic generation and PDF now work with
gemini-3.5-flash-lite after isolating and fixing nested provider schema maxima.
Prompts are version 1.2 following observed semantic calibration failures.
Twelve synthetic assessments completed (60 reviewer outputs and 60 PDF pages);
semantic screening still found an inconsistent claim status. Faculty approval, production
deployment and real JanMaang delivery remain pending. Simulation stays enabled.
This checkpoint supersedes historical pause/status notes below.

Plan: user-approved Independent AI Council, 2026-10-30.
Ruling: separate repository in the writable visualization workspace, outside both Hacktober Git roots; no source copied from ZIP.
Ruling: localhost standalone app is a single-user workspace; external hosting requires service authentication and JanMaang-proxied access.
Pre-flight: evidence contracts -> reviewer validation -> persisted report -> PDF -> integration wire contract.
Phase 1/2: tests written before implementation.

PAUSED at user request, 30 October 2026. Do not resume until asked.
Durable handoff: C:/Users/ARNAV_TFS/OneDrive/Documents/ChatGPT/Hacktober/AI_COUNCIL_HANDOFF.md
Phases 1-5 implemented. Phase 6 adapter and optional JanMaang integration implemented but disabled/unapproved.
Latest independent checks: 45 backend tests, 4 frontend tests, TypeScript/Vite build, 1 Chrome browser acceptance passed.
Main agent final checks: 129 API unit tests, mypy, Ruff, import boundaries; 7 council UI tests/TypeScript/ESLint passed.
Actual PostgreSQL and live Gemini acceptance pending; Docker unavailable. No merge, push, deployment or commits.
Review fixes: close SQLite connections, bound retry queue, remove full-source PDF appendix, persist retry keys.
Ruling: PDF references immutable source snapshots instead of copying whole source text, preventing source whitespace from amplifying PDF work.
Ruling: Docker loopback forwarding is explicit opt-in via COUNCIL_TRUST_LOOPBACK_PROXY; direct local mode remains strict.

Resumed at user request, 30 October 2026.
Final offline verification: 45 backend tests, 4 frontend tests/build, Chrome acceptance passed.
Main verification: 129 API unit tests; 144 UI tests serially; mypy, Ruff and import boundaries passed.
Real PostgreSQL acceptance: 4 cases pass, covering supervision/scope, concurrency, delivery retry and rollback.
Live probe found and fixed verified TLS trust and response_json_schema request incompatibility (RED/GREEN tests).
Live provider remains unapproved: configured model retired; replacement minimal/schema probes timed out.
Details and remaining limits: docs/verification.md. No production data was sent to the model.
Docker image build and disposable simulation smoke passed with optional trusted-CA BuildKit secret; test resources removed.


PAUSED AGAIN at explicit user request. No staging/commits/merge/push/deploy. Latest checkpoint in AI_COUNCIL_HANDOFF.md.

Resumed again at explicit user request. Final backend checks reverified: 45 independent and 129 JanMaang unit tests passed; Ruff, formatting, mypy and import boundaries passed.
Keeping both repositories and branches separate. Live provider acceptance and faculty approval remain pending; no production enablement.
