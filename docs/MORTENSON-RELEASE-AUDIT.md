# Mortenson release-readiness audit — November 17, 2026

Frontend baseline: `3f41a99e8bb459e9f4d6ae5a754cd73b878aeb18`.
Work stays on the existing feature branch and Draft PR #1. Main, backend main,
production credentials and deployments remain unchanged. Evidence is in
[`mortenson-final-review/`](mortenson-final-review/README.md).

## Five failing integration suites

The original five failures are reproduced in the paired logs committed under
`111326-login-fire-evidence/`. Clean main `ce47527` passed 4/10; feature `3f41a99`
passed 5/10. Main also had an obsolete Profile assertion. This audit does not
rewrite old baseline tests and pretend main passes the new design requirements.

| Suite | Exact cause at 3f41a99 | Predates redesign? | Defect or outdated test? | Resolution and retained coverage |
|---|---|---|---|---|
| `test-community-tools.py` | Strict locator `.community-tools` resolves to two sections on resources; includes at the top (`language weekly feedback`) and bottom (`weekly language`) duplicate language and weekly-tip UI. | Yes; same duplicate exists on clean main and its paired failure log. | Actual duplicate-content/interaction defect, not just a locator inconvenience. | Removed the redundant bottom include; kept interactive-first top panel and FAQ. Existing strict assertions retained. Full plan/quiz/check-in/hazard/volunteer/supply/FAQ and offline outbox recovery tests now pass. |
| `test-responsive.py` | Reads missing `#pnec-homepage-video` and old Elementor margin. Current approved home uses three photos. | Suite already failed on main's external-theme/negative-margin dependency; the missing-video failure is the redesign's expected replacement. | Outdated fixture contract. | Per `MORTENSON-REDESIGN.md` and `NAVIGATION-PREFERENCES.md`, checks current full-width hero bounds, exactly three images, no sidebar/padding, no horizontal overflow at all 12 inherited widths. Separate suite verifies timed rotation/focus/reduced motion. |
| `test-production-contract.py` | Asserts `_config.pages.yml` must not exist; it is explicitly authorized by `REVIEW_DEPLOYMENT.md`. Once corrected, browser origins also expose runner config mismatch. | Yes; same config assertion on main. | Outdated requirement plus test-build setup defect. | Validate documented separate review origin/base path/preview flag; preserve no-CNAME/no-.env/HTTPS/no-external-write assertions. Root contract plus independent project-path build/checks pass. |
| `test-admin-security.py` | HTTPS simulated page expects `https://api.pnec-review.invalid`; runner builds `_config.yml` with development `http://127.0.0.1:8425`. Handler abort/assertion makes navigation hang. | Yes; main has the same mismatch. | Test artifact built for the wrong environment, not proof of a broken auth gate. | Runner explicitly builds with the existing approved HTTPS test API. All 15 role/page combinations and ten actual login/return journeys remain. No denied-role assertion, CSRF check, retired-credential check or auth gate removed. |
| `test-media-release.py` | Same artifact-origin mismatch sends gallery/media requests to the development origin; handler assertion causes timeout. | Yes; same failure on main. | Test-build setup defect. | Same explicit HTTPS build input. Two same-name real multipart uploads must persist unique URLs, render two gallery images, and retrieve bytes from the HTTPS backend origin through isolated Flask. |

The runner's source default remains the documented development API; only the
isolated release artifact receives the HTTPS test API override. No production
endpoint is contacted. **Final full integration: 10/10 passed.**

## Additional actual defects found

- A delayed pre-login navbar identity response could clear credentials saved by
  a newer registration/login result. Introduced by the previous branch identity-
  clearing change. Auth-result/logout revisions now invalidate stale callbacks;
  deterministic regression preserves the newer token while keeping Account hidden
  until verified. Legitimate session rejection and backend checks remain intact.
- The conditional runtime API include introduced in the previous round no longer
  matched `build-pages.py`'s literal-assignment validator. Introduced by the branch.
  Added a distinct literal `PNEC_REMOTE_API_BASE`; the conditional `PNEC_API_BASE`
  still uses same-host loopback locally. Validator checks the rendered remote
  value across 40 pages, and browser contract checks actual HTTPS destinations.
- Branch theme overrides left legacy registration/volunteer foregrounds on pale
  surfaces; dynamic community cards and authenticated Profile retained white or
  gray surfaces/text in dark presets. New Sass token overrides fix these across
  all eight themes, including details, completion text and badge labels.
- Pre-existing faint checklist labels, unnamed image-only resource/event/About
  links, hidden-but-focusable neighborhood SVG, invalid donation-list semantics,
  unnamed kit progress and nested kit controls were verified and repaired safely.
  Enter on kit info previously toggled the item instead of the explanation; info
  and checkbox are now separate focusable controls. Regression covers independent
  info expansion, unchanged checkbox, Space toggle and persisted state.
- The unmodified backend does not register `announcements_bp`; public/admin
  requests return 404. Its frozen `0001_pnec_release` migration also omits the
  `announcements` table. These predate this frontend audit. The disposable launcher
  has an explicit `--enable-announcements` compatibility adapter using the existing
  model/routes/decorators; its marker discloses both repairs. This local table is
  additive synthetic state, **not a claimed backend release migration**.

[Proposed backend patch](backend-patches/register-announcements.patch) registers the
blueprint, adds frozen additive migration `0002_announcements` and updates the
readiness/seed revision. It refuses silent adoption of an existing unversioned
table and has no destructive downgrade. Verified in a separate temporary copy:
fresh migration, ready=0002, guest write401, resident write403, admin write201,
unapproved Origin 403, persisted public read. It is not applied to backend main;
backend owners must reconcile existing schema and version-specific tests before
acceptance. The legacy service on 8425 is untouched.

## Interactive acceptance matrix

| Feature | Actual local evidence | Scope / limitation |
|---|---|---|
| Registration/login/logout | Actual PNEC form registration, correct resident role, UI login, confirmed Account menu, logout revocation. | Synthetic accounts only; random fixture passwords remain in owner-private temporary files. |
| Dashboard/Profile | Real profile read, bio save/reload and account navigation; 24 authenticated theme/page axe checks. | Avatar/profile persistence and validation also covered by the isolated release suite. No real resident fields in screenshots. |
| Household and assessment | Real PATCH and quiz POST; ten questions; score, reload, SQLite persistence. | Account-owned records; another resident's user_id parameter never selects their record. |
| Check-ins/hazards | Actual form writes, reload, private resident lists, forged user/neighborhood parameters, resident moderation403. | Not emergency dispatch. Coordinator scope remains authoritative. |
| Volunteer | Coordinator UI posts synthetic shift; resident claims/cancels; last-slot full409; resident cannot see roster; cross-block coordinator write403. Actual interest-form submission. | Fixtures assign coordinator/admin roles only in the guarded disposable DB; public registration and profile updates cannot escalate roles. |
| Notification | Actual admin POST and resident403 on locally repaired backend; source label, keyboard dismissal, persistence and changed-version reappearance. | Live local compatibility adapter explicitly disclosed; unmodified backend still needs its separate patch/migration. |
| Themes/language | Real cross-route/reload persistence; eight presets, custom contrast validation, reviewed Spanish/reset. | Translation coverage is partial. |
| Speech | Mock contract tests for play/pause/resume/stop/page/selection/no-autoplay; native opt-in/stop/detection in Chromium, Firefox and WebKit. | Real voice inventories observed; audible output and screen-reader use require manual checks. |

Cookie-only integration checks retain HttpOnly/SameSite=Lax development cookies,
exact CORS, missing/unapproved CSRF rejection, valid-token acceptance, invalid
bearer rejection even with cookies, and role denial. No security control is
turned off. Source/database backups never include production data.

## Final automated results

- JavaScript: **9/9 passed**.
- Full frontend/backend integration runner: **10/10 passed** (all ten script names
  and exit codes in `integration-results.json`).
- Entire unmodified backend pytest suite in copied source: **194 passed**;
  7893 deprecation warnings. An initial harness omitted the backend `scripts/`
  directory; copying that required source fixed its backup-tool import. No test
  assertion or backend source was changed to get the 194 result.
- Root Jekyll/OCS Sass and Pages project build: passed; literal remote API verified
  in 40 rendered pages; links/assets verified in 41 HTML files.
- Redesign fixtures: **90** navigation and **160** route/viewport feature checks;
  **8 themes ×4 widths**, custom preferences, language, speech contract and new
  fire/login/offline/no-data tests passed.
- Native engines: **72 route/viewport checks** (eight pages ×3 widths ×3 engines),
  plus keyboard theme/language persistence and native audio detection.
- Axe4.11.0 WCAG2A/AA/2.1AA: **103** anonymous page/theme/viewport checks plus
  **24** authenticated Profile/checklist/volunteer checks. Zero violations in final
  runs. Incomplete rules remain recorded for human judgment; this is not an
  accessibility certification. The 103 matrix covers 18 major pages at 390/768/1280,
  plus seven core routes in every additional preset at 1280. The broader navigation
  and preferences suites also cover320px.
- Real8426 browser/API acceptance and separately migrated backend patch: passed;
  no identity/API mocks in those results. External providers blocked.

## Manual acceptance checks

These remain **unperformed**, rather than being inferred from automated passes:

| Check | Reviewer action | Acceptance / tracking |
|---|---|---|
| VoiceOver/NVDA | Read Home, mobile menu, Login/Register, signed-in Profile and all tools; inspect landmarks, dynamic errors and focus order. | Understandable names/reading order, no lost focus; issues2/11/14/15. |
| Audible speech | On the presentation machine, enable speech, choose a voice, hear Test Voice/read-selection/read-page, pause/resume/stop; disable and reload. | No autoplay, intelligible output, no private text read unexpectedly; issues14/15. |
| Physical touch/high zoom | Test mobile hardware and200–400% zoom, large system text, portrait/landscape and keyboard-only operation. | No clipped controls or obscured focus; issues2/5/11/15. |
| Photos/contrast | Inspect each rotating photo and all eight themes with real display/vision aids; axe cannot fully judge images/gradients. | Heading, fixed tip, forms and sources remain readable; issues3/11/14. |
| Content approval | Mr. Mortenson/content owner reviews legacy statistics/testimonials, source wording, translations and preparedness text. | No unsupported claim presented as verified; issues3/5/10/12/13. |
| Backend/release approval | Backend owner reviews announcement patch/migration, existing-table reconciliation, backup/restore/hosting and integration in an approved review environment. | Local success does not authorize production use; issues6/7/12/15. |

## Reproduction

Use the backend requirements and Playwright in an external venv; axe4.11.0 is a
local test dependency supplied by `--axe-script` and is not shipped in the site.
The test commands accept private file paths without printing passwords:

```sh
python -B scripts/run-release-tests.py --frontend-root "$PWD" --backend-root /path/to/pnec-backend-review
python scripts/test-local-preparedness.py --credentials-file <private-file> --output-dir /tmp/pnec-tools
python scripts/test-stakeholder-live.py --credentials-file <private-file> --output-dir /tmp/pnec-journeys
python scripts/test-browser-review.py --output-dir /tmp/pnec-engines
python scripts/test-review-accessibility.py --axe-script /path/to/axe.min.js --output-dir /tmp/pnec-a11y
python scripts/test-authenticated-accessibility.py --credentials-file <private-file> --axe-script /path/to/axe.min.js --output-dir /tmp/pnec-a11y-auth
python scripts/test-announcement-backend-patch.py --backend-root /path/to/pnec-backend-review --output-dir /tmp/pnec-patch
```

Existing Kanban stays open in Testing/In Progress. **Stakeholder-demo ready with
limitations; not merge/production ready.** No deployment, merge, main change or
new PR is part of this work.
