# 11/13/26 Redesign — Navigation, Homepage, and Personalization

Named for Mr. Mortenson’s feedback on November 13, 2026. Implementation began
November 16. Historical file paths and evidence remain available.

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
- One permanent, left-aligned homepage hero contains the heading, description,
  checklist button and Weekly Preparedness Tip. Only three real Poway background
  photos crossfade every eight seconds, sequentially without adjacent repeats.
  Numbered tabs, arrows, volunteering/fire slides and changing copy are removed.
  A single pause/resume button supports motion control; system or personal reduced
  motion stops rotation. Hidden documents suspend the timer. Without JavaScript,
  the first photo and all fixed content remain visible.
- Weekly Tip retains the existing `/api/preparedness/weekly` integration. Its
  section heading remains fixed; API titles/bodies are rendered with textContent,
  with the response week when supplied. Unavailable/empty/malformed responses
  retain the emergency-kit link and show the requested data-availability notices.
  No risk scores, threat classifications or emergency claims are rendered here.
  The four compact OCS action cards and their destinations are unchanged.
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
sidebar/hero/motion/theme extensions; no new framework or invented OCS API.

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
Three real photographs show Lake Poway (two views) and the Heritage Museum in
Old Poway Park. They provide local context, not current-incident imagery.

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

The execution host has Ruby 4. The source Gemfile now explicitly includes base64,
bigdecimal and kramdown-parser-gfm so normal bundle commands work without a
temporary Gemfile. Existing Jekyll/theme pins are unchanged. Node 24 and
Python/Playwright live outside the checkout.
The repository has no Makefile; its Jekyll commands and CI remain the build path.

## Approval required before merging

1. Review the draft PR diff and screenshots, then preview the feature branch at
   phone/tablet/desktop widths. Check sidebar, fixed hero/photo rotation, empty/API
   states, settings and your resident workflows.
2. Have the listed PNEC owners review their content/routes. Supply the missing
   fire-tree source if exact parity is required. Perform screen-reader/manual
   accessibility review and authenticated workflow acceptance.
3. Resolve or explicitly accept the documented pre-existing release-test gaps;
   verify the frontend CI result on the exact proposed commit.
4. Give explicit approval to merge the reviewed commit into main. No merge will
   be performed by this task. Any later deployment requires separate approval.

## Historical validation — November 16 implementation

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

Additional dark-mode visual review covered kit, checklist, volunteer, login,
profile access gate, events, resources, About and neighborhood screens. Legacy
kit labels, floating labels and fixed light form/map surfaces now consume
personal theme tokens. Targeted kit/login/volunteer checks guard the corrected
text and surface combinations; this is not a full WCAG certification.

## Weekly publishing mechanism — source verified November 17

Read-only inspection of `../pnec-backend-review/app/routes/preparedness.py`,
`weekly()` and `publish_tip()`, confirms GET `/api/preparedness/weekly` derives
Monday in America/Los_Angeles and selects current-week stored tips with general
or matching threat categories. Staff or higher can POST title/body/threat and
Monday `week_start`; database entries are not automatically authored each week.
No publishing scheduler was found. When no matching entry exists, the backend
returns one of four date-indexed educational tips (or threat-specific guidance).
That fallback changes by week on GET, without a scheduled job. The response has
no flag distinguishing editorial entries from its built-in fallback. The frontend
therefore labels all returned content as PNEC preparedness tips, without claiming
an editor published a new entry automatically. Production scheduling was not
inspected and no production request or backend edit was made.

## Styling audit — November 17

The redesign maintains Sass source only: `assets/css/ocs-pnec.scss` is a Jekyll
entry point importing `_sass/_ocs-pnec.scss`; appearance/sidebar/feature overrides
remain in `_sass/_mortenson.scss` and hero extensions in `_sass/_redesign-hero.scss`.
No new framework, handwritten CSS file or inline presentation was introduced.
The existing OCS variables, responsive-text/responsive-padding, main-container,
base-grid, grid-card-cell, text-button/base-button, inline-container and navigation
selector adaptation are reused. Spacing, radii, text sizes and transition durations
use the vendored scale where applicable. The toolkit contains no photograph
crossfade component or palette for PNEC; scoped hero colors and readability overlay
are explicit tokens. Theme surfaces and user fonts continue using shared CSS
custom properties. Legacy feature styles are preserved rather than rewritten.

## Current local preview

Build: `bundle exec jekyll build --destination /tmp/pnec-redesign-preview-8766`.
The existing loopback server serves this directory on port 8766:
`http://localhost:8766/` and `http://localhost:8766/pages/settings.html`.
This preview is static; the optional local backend remains `127.0.0.1:8425`.
Browser tests use explicit synthetic API fixtures; these are not shipped content.
New evidence is recorded separately in `111326-evidence/` to preserve prior images.

## Final feedback validation — November 17, 2026

- Normal Ruby 4 / Bundler build and Jekyll Sass compilation: passed.
- Project-base path checker: 40 generated HTML files passed.
- Offline JavaScript: 9/9 tests passed (Node 24.11.1).
- Navigation: 90 route/width checks passed at 320–1440px.
- Acceptance: 156 route/width checks passed at 320/390/768/1280px, including
  three loaded distinct photos, automatic no-repeat rotation, unchanged hero DOM
  and geometry, pause/reduced motion, permanent API tip and unavailable/empty/
  malformed responses, notices, appearance, drawer, resource and kit controls.
- Root and project-prefixed checklist destinations and settings persistence passed.
- Backend weekly tests (read-only source, disposable fixtures): 2 passed,
  39 deselected. No production API traffic or backend edits.
- Broader release runner: 4/10 passed on feature and clean `origin/main` at
  `ce475278ba406ddb4fa39a93daafb6dd3b5f7af7`, with matching failing suites and
  causes. Profile: unchanged contract assertion; community tools: duplicate
  `.community-tools` locator; legacy responsive: absent old element; production
  contract: existing `_config.pages.yml` assertion; admin/media: production API
  origin expectations versus local review routing. See paired results and
  failure-cause records in [current evidence](111326-evidence/).
- Screenshot API requests are unavailable fixtures, so images show the real
  unavailable-data UI, without invented tips or risk information.
- The existing helper auto-opens at the root homepage on window.load. Browser
  tests explicitly dismiss it for unrelated hero/navigation checks, then exercise
  its controls separately. This existing behavior is preserved.

Current screenshots: [desktop homepage](111326-evidence/home-1280.png),
[mobile homepage](111326-evidence/home-390.png),
[desktop dark settings](111326-evidence/settings-1280.png),
[mobile dark settings](111326-evidence/settings-390.png).

Full release readiness is **not** claimed. Existing failing suites, manual
screen-reader acceptance, content-owner review and authenticated end-to-end
verification remain open. PR #1 remains draft. No merge or deployment occurred.

Current results: **9/9 JavaScript tests**, **90/90 navigation route/viewport checks**,
**156/156 redesign route/viewport checks**, and **2/2 targeted backend weekly-tip
pytest checks** passed. Browser checks cover real image decoding, three unique
backgrounds, sequential rotation, fixed copy/geometry, checklist navigation,
published/empty/error/malformed tip responses, absent old controls, reduced motion,
settings and no page errors. Root and project-prefixed checklist/settings routes
were checked. External resources/API calls are mocked or blocked in browser QA;
no live authentication or current production tip availability is certified.

The ten-suite broader release runner was rerun against this feature and an
archived, unchanged `origin/main` at `ce475278ba406ddb4fa39a93daafb6dd3b5f7af7`.
Both pass SCSS, request-worker, quiz and account regression; both fail profile,
community tools, legacy responsive, production contract, admin security and media
release. Matching causes are recorded in the current evidence JSON files (older
widget/duplicate selector assumptions and review/API-origin contracts). The full
release suite remains **4/10**, so this is not full release readiness.

Current [desktop homepage](111326-evidence/home-1280.png),
[mobile homepage](111326-evidence/home-390.png),
[desktop settings](111326-evidence/settings-1280.png) and
[mobile settings](111326-evidence/settings-390.png) screenshots show the unavailable
API state with no synthetic published tip or emergency notice. Earlier screenshots
and acceptance evidence are retained under `mortenson-evidence/`.

The existing helper auto-opens at the root route on window.load; this behavior
was preserved. Hero/navigation tests explicitly dismiss it before interacting;
manual helper opening/closing and modes remain covered. Final user acceptance,
manual screen-reader review and live authenticated end-to-end checks remain open.

The same complete 90-check navigation and 156-check acceptance suites also passed
with the project-prefixed `/pnec-frontend-review/` build. Current environment and
aggregate results are recorded in `111326-evidence/validation.json`.
