# Production preparation — local verification and unresolved gates

Prepared in isolated worktrees/feature branches; frontend base `29902cf`, backend
base `159addd`. No push, merge, deployment, DNS/server migration or credential change.

## Results

- Production-root Jekyll/Sass build: 40 runtime API/base/preview/canonical values,
  41 HTML local path checks passed. Review project build: 40API/41 HTML checks passed.
- Production browser artifact: 27 route/viewport checks (9 routes ×3 widths), all API
  responses local fixtures. Correct root paths, canonical/API hosts, Login and
  unavailable-game fallback. No live authentication claim from these fixtures.
- Actual compatible frontend/backend: 10/10 cross-repository integration suites.
- Real loopback HTTP: household/quiz/check-in/hazard save/reload/SQLite persistence,
  registration/login/logout/Profile, multi-resident privacy, role/identity rejection,
  volunteer post/claim/cancel/capacity/interest and admin notification/dismissal/
  versioning passed. Prepared backend native schema 0002, zero compatibility fixes.
- Existing JavaScript: 9/9. Production live-release gate unit checks: 5/5, including
  duplicate/wrong CORS, review backend, old schema, missing PATCH/CSRF and invalid TLS.
- Backend: 204/204 pytest; 7935 deprecation warnings. Includes secure production-cookie,
  exact-origin, CORS/CSRF/role and migration creation/adoption/drift preservation.
- Workflow actionlint 1.7.12 passed; no workflow was dispatched. Existing review
  configuration/build/deploy files and backend frozen migration 0001 are unchanged.

## Independent verification still required

- Actual production publisher repository/domain binding and protected environment.
- Adya's service directory/account/upstream/commit inventory, correct vhost and TLS.
- Actual DB engine/version and live-schema clone adoption; SQLite + MySQL DDL
  compilation is not execution/recovery evidence for the server database.
- Consistent database/uploads backup, restoration and rollback-compatible code.
- Real proxy/client-IP rate-limit behavior, mail/reset delivery where in scope,
  approved synthetic hosted end-to-end tests and operational signoff.
- Inherited manual screen-reader/audio/touch and content/translation/game-deferral
  acceptance remains separate from this production-configuration preparation.
- Nginx/systemd are placeholder templates: neither is installed or server-validated.
- Explicit authorization for push/review/merge and each migration/publication step.

Both components are prepared local review candidates, NOT certified for deployment.
The next safe authorization is to push these two reviewed feature branches for code
review only; no merge/deploy until the owner/admin confirms the above gates.

See `PRODUCTION-PREPARATION.md` and the backend worktree's `deploy/ADYA-HANDOFF.md`.
Evidence is in `preparation-evidence/`; credentials are never included.
