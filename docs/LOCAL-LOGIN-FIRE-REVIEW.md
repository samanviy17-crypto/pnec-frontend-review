# 11/13/26 Redesign — Login, conditional sidebars, fire guidance and local tools

Work stays on `feature/mortenson-website-redesign-20261116` and draft PR #1.
Main, the existing backend checkout, production credentials and deployments are
unchanged. Earlier screenshots, route inventories and test evidence are preserved.

## Navigation

The five primary links remain Home, Prepare, Resources, Community and Profile.
A separate far-right Login control is visible on desktop and mobile. Its existing
PNEC destination is `/pages/register.html#login`; authenticated sessions replace
it with the existing account/role menu, My Profile and Sign Out. OCS's
[CSP top navigation](https://pages.opencodingsociety.com/navigation/courses/csp/)
was inspected for this placement/behavior; no OCS authentication API was copied.

Only confirmed sessions display account controls. A rejected session clears stale
identity/token caches; an unavailable backend retains credentials for a retry but
does not present cached identity as verified authentication. PNEC's original API,
logout, cookie, token, role and authorization mechanisms remain.

Home (including its Home-section routes) has no contextual sidebar element or
reserved sidebar padding. Its fixed content, three rotating photographs, Weekly
Tip, action cards and About section remain. Prepare, Resources, Community and
Profile retain their contextual sidebars. A shared route classifier avoids drift
between HTML layout and the header. The fire guide belongs to Resources even
when reached from Prepare's related link. Optional reading controls remain
available on Home without introducing a sidebar.

Styling uses the existing OCS navigation, grids/cards, containers, buttons,
spacing and responsive tokens in Sass partials. The tree diagram is native SVG
with keyboard-operated range controls, accessible labels/status and a complete
text explanation. No CSS framework or handwritten standalone CSS file was added.

## Why localhost login failed

Observed before changes, using read-only checks:

- An older Flask process from a different checkout occupied `127.0.0.1:8425`.
  `/api/health` returned 200; `/api/ready` returned 404. It did not identify itself
  as the isolated review backend. It was left untouched, along with its data.
- Its login OPTIONS response did not include `Access-Control-Allow-Origin` for
  `http://localhost:8766`. The current snapshot's default development allowlist
  also omits 8766. Browser CORS therefore prevents a usable account request.
- The frontend mixed `localhost` and `127.0.0.1` API addresses. Those are different
  sites for cookie purposes; an HTTP SameSite=Lax session must not be expected to
  work as a cross-site fetch merely because both names mean loopback.
- The frontend is a static Jekyll preview. Serving HTML on 8766 does not start a
  matching backend or configure its CORS. The prior preview was effectively
  disconnected from a compatible account backend, rather than a simulation of
  functional sign-in. The old generic internet-error text hid this distinction.
- Stale cached account data could keep Account visible after a failed identity
  check, masking the fact that no backend session had been confirmed.

The preview now uses the same hostname as its API and a temporary local-only
`local_api_port: 8426` Jekyll configuration. Production configuration is unchanged.
The default source fallback remains port 8425 for existing environments; the local
port override is explicit. All active API consumers honor the runtime API base.

## Disposable backend and security

`scripts/local-review-backend.py --backend-root <backend> --port 8426` copies only
application/migration source to a new private temporary directory. It copies no
`.env`, instance data, database, uploads or resident records. It generates a fresh
secret, runs the existing migration against a new SQLite database, and seeds one
synthetic resident and synthetic neighborhood. No admin is seeded. Provider and
publication secrets are cleared; outbound HTTP providers are blocked, so weather,
AI, email/provider and publication behavior are not presented as production data.

The server binds only to `127.0.0.1`. Its exact local CORS origins include
`http://localhost:8766` and `http://127.0.0.1:8766`; the existing CORS/CSRF middleware
remains enabled. Cookie HttpOnly/SameSite=Lax remains in effect. Secure=False is
the existing HTTP development setting, not a production change. `/api/health`,
`/api/ready` and an explicit `/api/local-review` marker identify the disposable
service. State and credentials are outside Git and protected by directory/file
permissions. The startup log prints the credentials-file path, never its password.

Current preview: frontend `http://localhost:8766`, API `http://localhost:8426`.
The old 8425 service is not used, killed, reconfigured or populated by these tests.
This is a synthetic review account environment; do not enter production credentials
or real resident information. Stop the created process before deleting its printed
state directory. Restarting the helper creates a new disposable database/account.

Reproduce with the existing external Ruby/Python environments:

```sh
# Terminal 1: run the compatible backend requirements in an external venv.
/path/to/venv/bin/python -B scripts/local-review-backend.py \
  --backend-root /path/to/pnec-backend-review --port 8426
# Open the private credentials.json path printed by this command for local login.

# Terminal 2: build for the disposable API, leaving tracked configs unchanged.
cat > /tmp/pnec-local-config.yml <<'YAML'
local_api_port: 8426
YAML
bundle exec jekyll build --config _config.yml,/tmp/pnec-local-config.yml \
  --destination /tmp/pnec-redesign-preview-8766
# Reuse the running 8766 server; start this only if that port is free:
python3 -m http.server 8766 --bind 127.0.0.1 --directory /tmp/pnec-redesign-preview-8766
```

## Complete preparedness audit

All four are **interactive sections containing forms**, not standalone working
buttons merely inferred from their appearance. They are included by
`pages/checklist.html` via `_includes/community-tools.html`, initialized by
`assets/js/pages/community-tools.js`, and use `pnecCommunityRequest()` in
`assets/js/api/preparedness-api.js` with the shared authenticated request worker.

| Feature | Frontend file | Action | Backend endpoint | Login required | Current status | Fix needed |
|---|---|---|---|---|---|---|
| Your Household Plan | `pages/checklist.html`; `community-tools.js: household()` | Loads the owned record; Save household plan submits household size, meeting point and evacuation/access plan. The Prepare link targets `/pages/checklist.html#household-plan`. | `GET/PATCH /api/preparedness` | Yes; any active account, including resident. | Actual local GET/PATCH, reload and SQLite persistence passed. Signed out: explicit login link; unavailable identity: backend-specific connection message. | API origin/CORS/cookie setup fixed; account check no longer silently treats an unavailable service as a confirmed signed-out session. |
| Preparedness Assessment | `pages/checklist.html#preparedness-quiz`; `community-tools.js: quiz()` | The home action card scrolls to the panel. Ten Yes/No choices are submitted by Save assessment; score/recommendations are shown from the backend response. | Public `GET /api/preparedness/quiz`; authenticated `GET /api/preparedness` and `POST /api/preparedness/quiz` | Questions endpoint is public; this UI and saving require an active account. No elevated role. | Actual ten-question submit, 100% result, reload and stored answers passed with synthetic data. Signed out now gets a login link before a question fetch can misleadingly report a quiz/network failure. | Connection fixed; sign-in gate reordered and empty-question data has a distinct availability notice. |
| Resident Well-Being Check-In | `pages/checklist.html`; `community-tools.js: checkins()` | Shows permitted existing statuses; Update my status writes Safe/Need help plus note; Remove my check-in deletes it. Explicitly not emergency dispatch. | `GET/PUT/DELETE /api/check-ins` | Yes; any active account. Submitting requires a neighborhood saved on the profile. | Actual PUT, scoped GET, reload and SQLite row passed. Signed out: login link. Missing neighborhood: Account Settings link instead of a doomed submit. | Connection fixed; missing-neighborhood prerequisite now explained before submit. |
| Report a Neighborhood Hazard | `pages/checklist.html#hazard-reporting`; `community-tools.js: hazards()` | Home card opens the section. User selects neighborhood/category and enters location/description; Submit hazard report POSTs and refreshes the permitted list. | `GET/POST /api/hazards`; moderation `PATCH /api/hazards/<id>` | Reporting requires an active account, including resident. Moderation requires coordinator or above and neighborhood authority. | Actual synthetic non-emergency POST, reload and SQLite row passed. Anonymous read is 401; resident moderation is 403. | Connection fixed; permissions retained; no emergency/real-resident data was posted. |

Database details and privacy:

- Household plan and quiz answers share the account-owned
  `household_preparedness` record. Its initial authenticated GET may create an
  empty owned record via the existing `record_for()` helper; actual plan values
  are saved by PATCH and quiz answers by POST.
- Check-ins use `resident_check_ins`, one row per user; PUT sets status/note/time
  using the user's profile neighborhood, and DELETE removes that user's entry.
- Reports use `hazard_reports`; POST persists the submitting user, selected valid
  neighborhood, category, location, description, time and initial status. Resident
  reads are scoped to their own data; coordinators see their neighborhood and
  staff/admin can see broader data. The existing service enforces these rules.
- No feature requires an admin account merely to submit personal information.
  Check-in/hazard lists are protected; no resident data is exposed to visitors.
- All recorded local values are explicitly labeled synthetic. These writes went
  only to the new temporary database; the legacy 8425 service received read-only
  health/readiness/preflight/public-question checks.

## Error and availability behavior

The shared worker distinguishes 401 sign-in, 403 role/security denial, 404 missing
resource, 4xx validation, server errors, unreadable responses, timeouts and network
failure. Loopback network failures identify the local API address and stopped/
CORS possibilities rather than blaming internet connectivity. Empty quiz data,
empty check-in/report lists and missing profile neighborhoods have separate UI.
Feature loading errors are live status/alert messages with an explicit reload
control; no write is retried automatically.

## Fire guidance source verification

Verification date: **November 17, 2026 (America/Los_Angeles)**.

- [Poway Municipal Code Chapter 15.05](https://ecode360.com/50659259): current
  codified Ord. 878 (2025), §15.05.050 modified CWUIC §§603.2, 603.4.2, 603.5,
  604.2–604.3.3. The first defines new-planting jurisdiction; the second specifies
  the 10-foot mature-drip-line and 20-foot canopy requirements for new trees in
  the 30-foot area and 10-foot chimney/stovepipe clearance for existing trees.
  [Signed Ord. 878, page 41](https://portal.laserfiche.com/Portal/DocView.aspx?id=172066&repo=r-23018445) records December 2, 2025 adoption and a 30-day effective-date clause; page 1 identifies January 1, 2026 for the state code edition. These dates do not establish a statewide Zone 0 commencement date.
  Local existing-building maintenance, permit/protected vegetation provisions
  and project-specific approvals remain distinct.
- [Poway Home Ignition Zones](https://poway.org/1147/Understanding-Home-Ignition-Zones)
  (canonical City page for the supplied civicplus alias): explicitly labels its
  existing-home guidance as best practices. It recommends 5 feet above roofs and
  10 feet from chimney/stovepipe outlets; that roof guidance is not represented
  as a universal new-tree planting law.
- [CAL FIRE defensible space](https://www.fire.ca.gov/dspace): zone priority,
  debris/vegetation maintenance, slope-dependent 10/20/30-foot canopy guidance.
  These generic recommendations do not replace stricter applicable local rules.
- [Board of Forestry Zones 0–2](https://bof.fire.ca.gov/projects-and-programs/defensible-space-zones-0-1-and-2)
  and [November revised rule package](https://bof.fire.ca.gov/regulations-and-policies/proposed-rule-packages).
  The September guidance PDF leaves its effective date blank and must not be
  treated as proof that a statewide compliance period began in September.
- [OAL emergency regulations under review](https://oal.ca.gov/emergency_regulations/emergency_regulations_under_review/):
  as checked, received November 16, 2026, file **2026-1116-02E**, Defensible Space
  Zone 0. Board adoption November 5 and submission do not establish an operative
  statewide date. This review did not verify an effective filing date and the
  page does not invent a statewide deadline.

The guide separates current local codified requirements, statutory jurisdiction,
pending statewide Zone 0 implementation and recommended safety practices. It
never says all existing Poway homes must apply the new-landscaping distances.
The diagram measures canopy edges, not trunks, and is illustrative rather than
an assessment of a parcel, slope, species or legal compliance.

## Verification and limitations

Detailed result JSON, screenshots and paired baseline records are in
`111326-login-fire-evidence/`. Browser fixtures and true local HTTP tests are
labeled separately. The unmocked test is `scripts/test-local-preparedness.py`; it
refuses non-loopback hosts and a backend lacking the explicit disposable marker.
It verifies UI login/logout, all four form writes and SQLite persistence, cookie-
only sessions, exact CORS, rejection of unapproved Origin/missing CSRF token,
success with a correct session token, invalid bearer rejection and resident
moderation denial. No security control is disabled in this preview.

Full release readiness is not claimed. Existing broader baseline gaps, manual
screen-reader/audio review, partial translation coverage and content-owner
review remain separate acceptance work. No merge or deployment is authorized.
