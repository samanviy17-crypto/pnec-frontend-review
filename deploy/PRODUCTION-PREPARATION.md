# PNEC production frontend — prepared, not published

These changes live in a separate local feature worktree based on approved
redesign `29902cf`. No push, merge, workflow dispatch, Pages setting, DNS change,
production API call, deployment or credential change is part of preparation.

## Two independent sites

| Purpose | Configuration | URL / API |
|---|---|---|
| Existing review | `_config.yml,_config.pages.yml` and existing `build-pages.py` | `https://samanviy17-crypto.github.io/pnec-frontend-review/`; existing separate review API policy unchanged |
| Production candidate | `_config.yml,_config.production.yml` and `build-production.py` | `https://powaynec.opencodingsociety.com/`; root baseurl; `https://powaynec-api.opencodingsociety.com` |

Do not assign the production custom domain to pnec-frontend-review's Pages site.
That would repurpose the review publisher. The owner must select a separate
production Pages repository in the samanviy17-crypto account; none is designated
by this preparation. The DNS CNAME already points to that account's GitHub Pages
host and must not be changed merely to select a different repository.

`_config.pages.yml`, `scripts/build-pages.py`, and the review deployment workflow
are unchanged. The shared path checker retains its review default and accepts an
explicit empty base only for production. The production builder checks every
rendered runtime API/base/preview value, rejects review-path leaks, verifies local
assets/links, and excludes developer/test documentation from the product artifact.
It does not read the review API variable or accept an arbitrary API override.

## Local preparation / offline CI

```sh
python3 scripts/build-production.py --destination /tmp/pnec-production-candidate
```

The new `Prepare Production Artifact (no deployment)` workflow is manual and
artifact-only. It has contents-read permission and no Pages/OIDC deployment
permission. Existing Frontend CI additionally validates the production artifact;
CI does not publish it. No workflow has been dispatched during this task.

## Dormant production publishing template

`production-pages-workflow.yml.example` is deliberately outside `.github/workflows`
and cannot execute here. After separate authorization, a repository administrator:

1. Confirms the separate production publisher; reviews the source and backend
   commit pair. Publishes neither an unreviewed branch nor an arbitrary SHA.
2. Installs the template only in that publisher, sets its nonsecret
   `PNEC_PRODUCTION_PUBLISHER_REPOSITORY` variable to its exact owner/repo, configures
   Pages source=GitHub Actions, and protects its `github-pages` environment with
   required reviewers/allowed branches. Never bypass those settings.
3. At the approved cutover, binds `powaynec.opencodingsociety.com` to that repository,
   verifies ownership/certificate provisioning and HTTPS enforcement. Do not
   transfer a domain away from another repository without confirming ownership.
4. Dispatches the manual template with the full reviewed frontend SHA after the
   backend is independently ready. The template refuses the review repository,
   requires the existing exact custom-domain binding, checks source provenance,
   and builds only after standard TLS health/readiness/CORS checks pass.
5. Approves the protected deployment environment only after artifact review.

The live API gate requires status=ok, review != true, readiness revision
`0002_announcements`, exactly one production CORS origin/credential header and a PATCH preflight with
Authorization, Content-Type and X-CSRF-Token.
It never bypasses TLS or logs credentials. It checks no private resident records
and performs no API writes. Additional authenticated/role/database acceptance
must be performed in an approved synthetic environment before cutover.

## Release gates

The audit found missing production Pages binding, invalid custom-host certificates
and an unrelated backend upstream. Local tests cannot fix or verify those server
settings. Adya must complete the backend repository's `deploy/ADYA-HANDOFF.md`.
Actual database-engine/adoption rehearsal, backup/restore and rollback approval,
production publisher selection, protected environment enforcement and explicit
merge/deploy authorization remain blockers. A prepared artifact is not a deployed
website or production-readiness certification.

Frontend rollback: retain the prior reviewed artifact/SHA and verify its API
compatibility before republishing it. Never change DNS as an automatic rollback.

Production also retains the approved review build's explicit unavailable RPG
message and working quiz link. Setting review_preview=false must not reactivate
the missing game engine. The route is preserved; game implementation/deferral
acceptance remains a content-owner release decision. No gameplay claim is made.
