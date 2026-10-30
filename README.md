# AI Council
Independent student-project review workspace. Five perspectives examine findings,
methods and evidence and produce a detailed, evidence-linked PDF. No grades,
badges, automatic approvals, or execution of uploaded source code.

## Local setup (Windows PowerShell)
Requires Python 3.12+ and Node 22+.
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
Copy-Item .env.example .env
npm.cmd --prefix web ci
npm.cmd --prefix web run build
.\.venv\Scripts\python.exe -m uvicorn council.main:create_app --factory --host 127.0.0.1 --port 8090
```
Open http://127.0.0.1:8090. Use **Load example** for a complete demonstration.
On Linux/macOS substitute `.venv/bin/python` for the Windows executable path.
For frontend development run the backend as above and `npm --prefix web run dev`;
Vite proxies API calls to the backend. No external services are needed.

## What is real
Evidence validation, immutable snapshots, SQLite persistence, retry handling,
progress, report history and PDF generation are implemented. In the default
**simulation** mode all five critiques are deterministic placeholders, marked as
simulation in the UI and every PDF page. They do not semantically evaluate claims.

A live Gemini adapter is deliberately gated behind model/key configuration,
service authentication and explicit human quality approval. See
[operations](docs/operations.md) and [integration contract](docs/integration.md).
Never distribute the service key to a browser. Integrated users access the council
through JanMaang's authenticated backend, not the standalone service UI.

## Boundaries
Separate Git history, dependencies and deployment from JanMaang. No shared source
imports, source vendoring, or direct business-database access. JanMaang stores
supervisor assignments, assessment linkage and publication state; council
implementation and reviewer prompts remain here.

Accepted evidence: UTF-8 text, Markdown, CSV and selected source files. No remote
repository fetches, archive extraction, PDF/DOCX parsing, code execution or
independent factual verification. Reports are English; supported Unicode glyphs
are embedded, and unsupported characters appear as explicit U+ code points.

## Checks
```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check council tests
npm.cmd --prefix web test
npm.cmd --prefix web run build
# Install Chromium once, or use an installed Chrome:
$env:PLAYWRIGHT_CHANNEL = 'chrome'
Push-Location web
npx.cmd playwright test
Pop-Location
```
CI runs the offline backend, frontend and browser-to-PDF workflow without secrets.
Completed checks and remaining live-service limits: [verification record](docs/verification.md).

## Provenance
Written independently from the supplied ZIP. Its original code, licence and
authorship could not be verified and no source was copied. The bundled unmodified
DejaVu font has its own licence in `council/fonts/LICENSE-DejaVu.txt`.
No licence for this project's own source is selected; decide one before public redistribution.
