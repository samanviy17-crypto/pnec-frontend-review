# Local production-preparation evidence

Frontend base `29902cf`; backend base `159addd`. Both changes are isolated local branches.
No production secrets/data or server writes are involved.

- `integration-results.json` / `integration-run.txt`: 10/10 cross-repository suites against the prepared backend.
- `preparedness-live-results.json`: real localhost HTTP login/logout, persistence and security.
- `stakeholder-native-results.json`: real HTTP registration/Profile/privacy/volunteer/notice/preferences; native schema 0002, no compatibility adapter.
- `production-artifact-results.json`:27 production-host browser checks with anonymous API fixtures; all traffic local. Not an authentication claim.
- `production-gates.txt`: 5 offline negative/positive release-gate tests, including duplicate CORS, old schema, missing PATCH/CSRF and TLS failure without insecure retry.
- `build-summary.txt`: separate production and preserved project-review builds/path checks, plus workflow lint.
- `javascript-tests.txt`: 9/9 existing JavaScript tests.

The backend worktree contains its own 204-test summary and source/schema tests.
Nginx/systemd templates are inert placeholders, not server-validated configuration.
MySQL execution, actual server provenance/TLS/CORS/proxy limits, backup restore,
production publisher/protected environment and explicit release approval remain gates.
