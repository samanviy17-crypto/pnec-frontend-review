# Current Mortenson review evidence

Prepared November 17, 2026. Changes since frontend `3f41a99`; backend input `159addd`.
[Demo order/URLs](../MORTENSON-DEMO.md) · [Release audit](../MORTENSON-RELEASE-AUDIT.md).

## Screenshots

| Page | Desktop1280 | Mobile390 |
|---|---|---|
| Home/no sidebar and synthetic banner | [Desktop](home-1280.png) | [Mobile](home-390.png) |
| Prepare/checklist | [Desktop](checklist-1280.png) | [Mobile](checklist-390.png) |
| Resources | [Desktop](preparedness-resources-1280.png) | [Mobile](preparedness-resources-390.png) |
| Community | [Desktop](community-events-and-activities-1280.png) | [Mobile](community-events-and-activities-390.png) |
| Fire safety | [Desktop](fire-safety-1280.png) | [Mobile](fire-safety-390.png) |
| Preferences | [Desktop](settings-1280.png) | [Mobile](settings-390.png) |
| Empty login form panel | [Desktop](register-1280.png) | [Mobile](register-390.png) |
| Public Profile | [Desktop](profile-1280.png) | [Mobile](profile-390.png) |
| Volunteer | [Desktop](volunteer-1280.png) | [Mobile](volunteer-390.png) |

Anonymous screenshots contain no account credentials or private resident fields.
Login captures only its empty form panel, excluding legacy testimonial copy.
Synthetic notice text is explicitly labeled; it is not an official emergency.
Some inherited external images are blocked by the offline-safe audit policy.

## Results

- `integration-results.json`, `integration-run.txt`: all ten release suites and exit codes.
- `backend-tests.txt`: complete unmodified backend pytest summary (194 passed).
- `stakeholder-live-results.json`, `preparedness-live-results.json`: real local HTTP/UI writes/security/privacy. Local announcement repairs are explicit in metadata.
- `backend-patch-results.json`, `backend-patch-run.txt`: proposed backend patch applied ONLY to copied source, fresh migration/readiness and actual HTTP authorization/CSRF.
- `browser-engine-results.json`: Chromium/Firefox/WebKit 72 route/viewport checks and native speech detection. No audible assertion.
- `accessibility-results.json`: 103 anonymous page/theme/viewport checks; zero axe violations; incomplete rules preserved.
- `authenticated-accessibility-results.json`: 24 actual signed-in theme/page checks; zero axe violations.
- `redesign-*.json`, `redesign-run.txt`: four existing fixture-based suites (navigation 90; features 160; preferences 8 themes×4widths; fire/login/error states).
- `project-build.txt`, `javascript-tests.txt`: project API/path verification and 9 JavaScript tests.

Automated results are not a screen-reader certification, a production-data test,
or permission to merge/deploy. Manual and backend release gates stay open.
