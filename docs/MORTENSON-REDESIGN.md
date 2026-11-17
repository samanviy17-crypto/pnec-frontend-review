# Mortenson redesign — November 16, 2026

This is an isolated, unmerged frontend change. No deployment or production change
is authorized. Worktree: `../pnec-redesign-20261116`; branch:
`feature/mortenson-website-redesign-20261116`. Base: freshly fetched `origin/main`
at `ce475278ba406ddb4fa39a93daafb6dd3b5f7af7`. The original main worktree was clean
and remains untouched. No backend edits, migrations, API changes or credentials.

## Before and after

- The fixed horizontal header becomes one fixed left sidebar on desktop, with
  the same data-driven groups, destinations, current-route styling and existing
  account IDs. On tablet/phone it becomes a modal drawer with Escape, backdrop,
  focus containment/return, inert background, scroll containment and native
  button disclosures. Account role gating remains in the existing auth code.
- The static hero becomes four topic slides: preparedness, the actual published
  Weekly Tip, volunteering and fire safety. Previous/next, labeled indicators,
  keyboard arrows, pause/resume, focus/hover/visibility pause and motion
  preferences work without moving keyboard focus. Rotation is off for reduced
  motion. The four compact OCS action cards are preserved byte-for-byte.
- Weekly Tip reads the existing `/api/preparedness/weekly` response, including
  published title/body and week attribution. Failure/empty responses say the tip
  is unavailable and retain the kit link. No synthetic tip is shipped. The old
  static tip card is replaced by a persistent preparedness action card.
- Existing staff-managed announcements use the same `/api/announcements` API,
  with text-only rendering, severity labels, update metadata, versioned
  dismissal and expiry checks. Priority notices cannot be dismissed. No content
  is displayed for empty/unavailable API responses.
- The API has no emergency-verification field. Its messages are explicitly
  community notices, never official emergency alerts. Optional, repository-
  reviewed official notices can be authored in `_data/community_notices.yml`.
  The list ships empty. They require `verified: true`, a nonfuture `updated_at`,
  a future `expires_at`, and an HTTPS source on the explicit official-domain
  allowlist in `announcements.js`. They are nondismissible and show the source,
  issuance and expiry. This is an editorial verification workflow, not a live
  emergency feed; an allowlisted URL alone does not prove a message is accurate.
- Appearance & Settings is available without an account: light/dark/system,
  plain/soft/grid backgrounds, sans/serif/monospace fonts, three text sizes,
  line spacing, motion reduction and reset. Choices are allowlisted and stored
  under `pnec_appearance_v1`. Corrupt/blocked storage falls back safely. The
  existing authenticated profile contract supports no appearance fields, so
  preferences remain browser-local for both visitors and signed-in residents.
- The shared shell compacts content across all pages. Resource actions, topic
  shortcuts, expandable guidance and search precede the existing reference
  library. Kit item search preserves the existing checklist/progress/persistence.
  Existing household, quiz, shift, map and hazard interactions are retained.
- Route-wide QA also fixed narrow admin-map action overflow and the admin
  page's duplicate `errors.js` include. The shared layout loads that script once,
  before consumers; constants, API origin and request logic are unchanged.

## OCS components and visual references

The actual vendored variables, grid, buttons, containers and navigation are listed
in [REDESIGN.md](REDESIGN.md). This change continues those imports and uses
`grid-card-cell` and OCS spacing tokens in `_sass/_mortenson.scss`. It adds scoped
sidebar/carousel/motion/theme extensions; no new framework or invented OCS API.

Visual references inspected in the related OCS-based pages source at
`bb2d8a291337bf9bcfab782679cbf71c76d1e2b3`:
`_sass/open-coding/dashboard-v2.scss` (`.ocs__dashboard-card`, panel/border tokens,
compact spacing) and `_sass/open-coding/grading.scss` (`.grading-btn`, typography
and button spacing). No grading/account business logic was copied.

The shared semantic tokens are surface, background, text, muted text, border,
accent, font, size and line height. Theme-resolved values override the old main
white gradient and fixed paragraph colors. The grid background uses low-opacity
lines. Stable sidebar dimensions are independent of font selection. Mobile
controls stay at least 44px tall. Existing feature-specific styles remain where
needed rather than rewriting working forms.

Photo sources, licenses and transformations are in [ATTRIBUTION.md](../ATTRIBUTION.md).
Two real Lake Poway photographs are shared across the four topics; they are
landscape context, not staged volunteer or current-incident imagery.

## Review evidence and preview

[Route inventory and interaction audit](MORTENSON-ROUTES.md).
[Complete changed-file list](MORTENSON-CHANGED-FILES.md).
Screenshots use empty mocked API reads, no fabricated resident data or notices:

- [Desktop homepage](mortenson-evidence/home-1280.png)
- [Phone homepage](mortenson-evidence/home-390.png)
- [Desktop dark settings](mortenson-evidence/settings-dark-1280.png)
- [Phone dark settings](mortenson-evidence/settings-dark-390.png)

On a supported Ruby/Jekyll environment:

```sh
cd /path/to/pnec-redesign-20261116
bundle install
bundle exec jekyll build --config _config.yml,_config.pages.yml --destination /tmp/pnec-mortenson-site
mkdir -p /tmp/pnec-mortenson-preview
ln -sfn /tmp/pnec-mortenson-site /tmp/pnec-mortenson-preview/pnec-frontend-review
python3 -m http.server 8766 --bind 127.0.0.1 --directory /tmp/pnec-mortenson-preview
```

Open `http://127.0.0.1:8766/pnec-frontend-review/` and
`http://127.0.0.1:8766/pnec-frontend-review/pages/settings.html`.
The static preview preserves its existing disconnected-review warning. Local
backend requests still target `127.0.0.1:8425`; full account workflows require a
separate disposable local review backend. Do not substitute production.

The execution host has Ruby 4; local builds used the already available temporary
`BUNDLE_GEMFILE=/tmp/pnec-tools/Gemfile` compatibility bundle, without modifying
source dependency pins. Node 24 and Python/Playwright live outside the checkout.
The repository has no Makefile; its Jekyll commands and CI remain the build path.

## Approval required before merging

1. Review the draft PR diff and screenshots, then preview the feature branch at
   phone/tablet/desktop widths. Check sidebar, four carousel topics, empty/API
   states, settings and your resident workflows.
2. Have the listed PNEC owners review their content/routes. Supply the missing
   fire-tree source if exact parity is required. Perform screen-reader/manual
   accessibility review and authenticated workflow acceptance.
3. Resolve or explicitly accept the documented pre-existing release-test gaps;
   verify the frontend CI result on the exact proposed commit.
4. Give explicit approval to merge the reviewed commit into main. No merge will
   be performed by this task. Any later deployment requires separate approval.

## Validation — local results

- Existing JavaScript suites: **9 tests passed**, Node 24.11.1, `npm test`.
- Jekyll 3.9.5 plus vendored OCS Sass: **passed** via the temporary Ruby bundle.
- `scripts/check-pages-paths.py`: **passed**, assets/links/srcsets/scripts across
  40 generated HTML files (includes the generated navigation data view).
- Existing navigation browser regression: 15 routes at six widths (320, 390,
  768, 1024, 1280, 1440), stationary shell/link boxes, actual link transitions,
  keyboard/touch disclosures, role-gated account presentation, 4/2/1 action
  cards, helper modes, no overflow or uncaught page errors.
- New browser acceptance: 39 application HTML routes at four widths, **156
  route/viewport checks**, plus weekly API fixtures, unavailable/empty states,
  safe/versioned notices, nondismissible official-notice validation, mobile
  focus/inert behavior, theme/font/size persistence, reset, corrupt/blocked
  storage, kit search/checklist persistence, resource search/disclosures,
  automatic rotation, focus pause and reduced motion. Browser API responses
  are synthetic fixtures, never presented as a live-backend verification.
- The browser helper allocates an ephemeral loopback port so isolated worktrees
  can run concurrently. Frontend CI runs both suites and uploads review evidence.
- `git diff --check`: passed.

The broader cross-repository release runner was also executed, using the same
unchanged backend checkout, temporary SQLite databases and blocked external
providers, against **both this branch and clean main at ce47527**:

| Suite | Feature branch | Baseline main |
|---|---|---|
| SCSS ownership/output | Pass | Pass |
| Request worker | Pass | Pass |
| Quiz | Pass | Pass |
| Account regression | Pass | Pass |
| Profile | Fail | Fail |
| Community tools | Fail | Fail |
| Legacy responsive | Fail | Fail |
| Production contract | Fail | Fail |
| Admin security | Fail | Fail |
| Media release | Fail | Fail |

Failing suites reference older homepage widgets/video, an obsolete prohibition
on `_config.pages.yml`, and mocked production-origin expectations that disagree
with current review routing. Identical pass/fail outcomes on baseline are
evidence these failures predate this implementation, not proof their underlying
workflows are correct. These remain acceptance gaps; **the full release suite
does not pass**. It would be inappropriate to close the related Kanban issues
or claim production readiness. Logs/artifacts for this session are under
`/tmp/pnec-mortenson-*.log` and the disposable release artifact directories
printed by the runner.

Read-only Render check: `/api/ready` returned 200/ready with the expected GitHub
Pages CORS origin; `/api/health` timed out at 45 seconds. No live signups, saves,
hazard reports, volunteer changes or production writes were performed. Live
end-to-end account/API acceptance is still required.

Manual screen-reader review, individual content-owner signoff and exact fire-tree
comparison remain pending. The legacy RPG limitations in RPG-LIMITATIONS.md are
unchanged. No new backend appearance fields were added. Official emergency
notices remain unconfigured until a real source is reviewed by the PNEC owners.

CI portability correction: backdrop dismissal tests use the measured element
width so the click avoids the non-overlay Linux scrollbar gutter. The same
visible dismissal behavior remains covered on macOS and Linux.
