# Operations
## Local-first deployment
One process, one Uvicorn worker, one private persistent volume. SQLite and PDFs
must survive container restarts. `docker compose up --build` exposes only
127.0.0.1:8090. Never scale this configuration horizontally: restart recovery and
in-process serialization assume exactly one service process.

Compose explicitly enables COUNCIL_TRUST_LOOPBACK_PROXY because Docker forwards
host-loopback connections from its bridge address. Keep the published port bound
to 127.0.0.1. Do not enable this setting behind a publicly accessible proxy without
service authentication. Normal direct Python execution leaves it false.

If HTTPS is intercepted by an organization-trusted CA, supply its verified public
CA bundle at build time without disabling TLS:

```powershell
docker build --secret id=ca_bundle,src=private/build-ca.pem -t ai-council .
```

The optional BuildKit secret is used only by npm/pip and is not copied into the
image. In a Linux runtime that also needs the organization's CA, mount a trusted
PEM bundle read-only and set SSL_CERT_FILE to that mounted file. A successful
build does not configure runtime trust. Never commit private keys, disable
verification, or enable a live student deployment merely to work around trust.

## Private storage and backups
The data directory contains student evidence in `council.sqlite3` and report
artifacts in `reports/`. It is not mounted as static content. Keep OS directory
permissions restricted to the service account and use an encrypted persistent
disk where appropriate. Do not commit backups or credentials.

Stop the service before backing up; copy the entire data directory (including WAL
files if present). Restore it as one unit before restarting. Startup marks queued
or running assessments incomplete rather than guessing that work succeeded.
Only incomplete assessments may be explicitly retried. Completed assessments are
immutable and publication failures must not trigger a new model assessment.

For cleanup, stop the service, back up first, then remove both selected assessment
rows and their snapshot/artifact together in a transaction using a reviewed
administrative procedure. No automatic retention policy deletes student work.
After restoring, check report history and PDF download before accepting submissions.

## Live gate
1. Review `evals/`, supply human-checked examples and run the evaluation process.
2. Set COUNCIL_GEMINI_KEY and a currently supported COUNCIL_GEMINI_MODEL server-side.
3. Set a randomly generated COUNCIL_SERVICE_KEY (at least 32 characters).
4. Set COUNCIL_LIVE_QUALITY_APPROVED=true only after faculty sign-off, then
   COUNCIL_MODE=gemini. Changing a flag is not evidence that quality was tested.
5. Configure JanMaang's matching service URL/key; keep the council behind a private
   network or HTTPS endpoint. The standalone UI does not accept service secrets.
6. Verify an authorized student/faculty round trip and unrelated-account denial
   before making the feature available. Optional integration is disabled by default.

Do not reuse local simulation artifacts as live reports. Monitor incomplete
assessments, provider errors, pending publication, disk usage and backups. Logs
identify assessment failures by ID/type; do not log raw evidence or provider keys.
Provider spend is bounded per assessment, not per deployment: set provider billing
quotas and control who may submit in JanMaang.

## Limits
20 files, 50,000 characters per file, 200,000 total evidence characters, 1 MB JSON
request, 10 queued/running assessments, at most 100 recent history entries.
All bounds are rejected explicitly; evidence is never silently truncated.
A timeout or malformed reviewer output leaves an incomplete assessment without a
completed report. No web search or code execution tools are enabled.
