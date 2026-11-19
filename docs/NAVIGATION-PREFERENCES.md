# 11/13/26 Redesign — two-level navigation and Profile preferences

This follow-up stays on `feature/mortenson-website-redesign-20261116` and draft
[PR #1](https://github.com/samanviy17-crypto/pnec-frontend-review/pull/1).
Main, production configuration, credentials and backend source are unchanged.
The approved fixed-content hero and its three real rotating photographs remain.

## Reference implementation inspected

The actual [OCS dashboard](https://pages.opencodingsociety.com/dashboard) was
inspected on November 17, 2026, including its loaded
[`preferences.js`](https://pages.opencodingsociety.com/assets/js/pages/dashboard/preferences.js)
and [`preferences-layout.js`](https://pages.opencodingsociety.com/assets/js/pages/dashboard/preferences-layout.js).
The current swatch implementation uses a sample panel, accent bar, theme name and
pressed state; the appearance layout organizes presets, fine-tuning and a live
preview with contrast feedback. Those patterns are adapted here. No separate
appearance screenshot was present in the supplied attachment; the live page and
its actual implementation were the visual/source reference.

Also inspected the OCS-based local source at
`/Users/samanviyachareni/opencs/pnec-public-kanban`, commit
`7dc1e9915d0f506bdbd24c287d8b164cfce9bc6f`: `_layouts/dashboard-v2.html`,
`assets/js/user-preferences.js`, dashboard preferences module,
`_sass/open-coding/dashboard-v2.scss`, navigation and toolkit mixins. The existing
vendored toolkit and Apache-2.0 license remain in `_sass/vendor/ocs/`.

Reused/adapted:
- OCS/Minima `site-header`, `wrapper`, `site-title`, `site-nav` structure and
  scoped navigation selectors, adapted to the requested five PNEC categories.
- `base-grid`, `grid-card-cell`, `main-container`, `inline-container`,
  `text-button`, `base-button`, `responsive-padding`, plus spacing, text, radius
  and transition tokens.
- OCS `.ocs__prefs-swatch` sample/name/accent-bar structure and `aria-pressed`
  selection pattern, its preset palette family, and live-preview luminance math.
  PNEC retains its own Site Default; Light/Sepia text and several accent colors
  are adjusted for readable contrast. Sunset is a PNEC extension.

The OCS controller also contains Spring account synchronization, course/admin
logic, AI themes and head tracking. Those are incompatible with the existing PNEC
contracts and are not imported. This implementation uses the established
`pnec_appearance_v1` browser-local preference key, including migration by defaults
for old records. No new backend endpoints or migrations.

## Navigation and route audit

The top bar has exactly **Home, Prepare, Resources, Community, Profile**.
Each link visits an existing landing route; a single contextual sidebar is shown
for that route. There are no duplicate landing pages. Hash changes select the
appropriate contextual group, including hazard reporting within Community.

| Category | Existing destinations |
|---|---|
| Home | `/`, `/#about-pnec`, `/#weekly-tip-heading`, About details, Contact |
| Prepare | checklist/dashboard, checklist anchor, household plan, quiz, kit, role quiz |
| Resources | library, fire/earthquake guidance anchors, hazard context, programs/services, archive, security/privacy, additional legacy resource links |
| Community | events, volunteering, shifts, supply drives, neighborhoods, hazard reporting, gallery, blog/articles, donations |
| Profile | `/pages/profile.html`, `/pages/settings.html`, `/pages/profile.html#account-settings` |

`_data/ocs_navigation.yml` is the category inventory. Existing `pnec_nav.yml`
manager additions remain available under Resources when not already mapped.
Blog detail routes remain Community; onboarding/auth/account/admin routes remain
Profile. Existing routes, including `/pages/about.html`, remain addressable.
About PNEC is a visible homepage section, not a sixth top-level category.

All internal links use Jekyll `relative_url`. The existing account/role worker
still controls the same navigation IDs: coordinator media/events; staff dashboard;
admin dashboard, theme/navigation/blog/volunteer/security/map/analytics tools.
These are visibility controls; existing backend/page authorization remains
necessary and unchanged. No cached user is used to populate the private profile.

Desktop: fixed 80px top bar and 264px contextual sidebar below it. Mobile/tablet:
the navigation trigger opens one modal drawer containing the five category links
and current context. Escape, backdrop dismissal, focus containment/return, inert
background and resize handling are preserved. Links remain native anchors,
expandable account/admin groups use native details/summary, and primary links
support ArrowLeft/ArrowRight/Home/End in addition to normal Tab navigation.

## Profile and appearance

The existing profile is the Dashboard and authenticated account overview. Its
account editing, avatar, neighborhood, validation, completion/badges and sign-out
features are retained. Account Settings links to its existing editor. A 401 shows
a login prompt with public Preferences access and no private fields. Backend
unavailability shows an error/retry plus login/preferences links, without treating
an unknown session as authenticated.

The preference page uses eight keyboard-selectable theme cards: Site Default,
Midnight, Light, Green, Sepia, Cyberpunk, Ocean and Sunset. Preset selection,
fonts, text sizes, background pattern/tint, button style, line spacing and reduced
motion apply/save locally and persist across pages and refreshes. Site Default
continues supporting system/light/dark mode. Reset restores appearance defaults
while retaining separately managed language/audio choices.

Custom hex colors preview within the sample first. Save applies them site-wide
only if body text and accent have at least 4.5:1 contrast against the background.
Button foreground is selected for contrast. Corrupt/untrusted stored colors,
preset names, font names and language codes are validated; unusable palettes fall
back to the selected preset. Blocked storage uses in-page settings with an honest
status message. Runtime style changes are limited to necessary validated color
custom properties; layout, presets and typography remain Sass source.

## Language coverage

OCS's site translator injects Google Translate and controls translation cookies.
It was reviewed but is not copied: applying an external DOM translator to PNEC's
account forms and private content would introduce a new integration with different
privacy/security behavior. PNEC instead supplies a local, reviewed English/Spanish
dictionary for marked navigation and preference labels. No external translation
requests, cookies or backend language migration are introduced.

English remains the default and the document's content language. Individually
translated labels carry `lang="es"`. The saved language persists across pages;
Reset to English is available. Guides, form options, user content, API messages
and other unmarked text retain their original language. This is **partial UI
translation**, not full Spanish site coverage. Full translated guides/content
would require reviewed translations or a separately accepted translation provider.

## Audio coverage

Speech uses the browser's `speechSynthesis` and `SpeechSynthesisUtterance` APIs,
without microphone access, server audio or playback on page load. Controls include
enable/disable, available voice, speed, pitch, volume, Test Voice, pause/resume and
stop. Once enabled, contextual reading controls can read the page's suitable main
text or explicitly selected text. Form controls, scripts and hidden text are
excluded from page reading. Long text is chunked; page navigation cancels pending
speech. A separate test verifies the no-support fallback.

Preferences persist locally; unavailable voices fall back to the browser default.
Real voice inventory and audible output depend on browser/OS support. Automated
speech tests use explicit voice/utterance fixtures to verify arguments, controls,
selection, persistence, no autoplay and no-support behavior; they do not certify
real audio quality, pronunciation, installed language voices or screen-reader
compatibility. Manual screen-reader/listening checks remain open.

## Validation and evidence

Commands (tools are installed outside this worktree):

```sh
bundle check
bundle exec jekyll build --destination /tmp/pnec-redesign-preview-8766
bundle exec jekyll build --config _config.yml,_config.pages.yml --destination /tmp/pnec-navprefs-project-site
python3 scripts/check-pages-paths.py --site /tmp/pnec-navprefs-project-site
npm test
bash scripts/check-redesign-browser.sh /tmp/pnec-navprefs-project-site /tmp/pnec-navprefs-project-evidence
python3 scripts/run-release-tests.py --frontend-root "$PWD" --backend-root ../pnec-backend-review
```

The browser helper now runs the existing navigation/homepage suites and the new
`test-profile-preferences.py`. It verifies five category transitions and one
contextual group, destinations, stationary desktop geometry, keyboard/mobile
modal behavior, four roles, eight themes at four widths, storage, safe color
previews/contrast rejection, fonts/buttons, reviewed language, speech protocol and
its unsupported fallback. Prior hero/API/notice/kit/resource tests remain.

The existing profile integration assertion was updated for the explicitly
requested signed-out dashboard prompt, rather than expecting the old redirect.
Registration, authenticated edits, validation, ownership, database persistence,
logout and the absence of private fields after logout remain tested. Main's
unchanged profile suite fails earlier at its old missing homepage risk-widget
expectation; this is recorded separately rather than calling the two profile
outcomes equivalent.

New screenshots and paired release results live in
`111326-navigation-preferences-evidence/`; all earlier evidence is preserved.
Screenshots use unavailable/401 API fixtures and no invented resident records.

Local preview: [Home](http://localhost:8766/),
[Profile Dashboard](http://localhost:8766/pages/profile.html),
[Preferences](http://localhost:8766/pages/settings.html),
[Account Settings](http://localhost:8766/pages/profile.html#account-settings).
The local backend remains optional at `127.0.0.1:8425` and was not exposed publicly.

No merge, deployment or production-readiness claim is made. Existing broader
release-test gaps, manual accessibility/listening review and full translation
coverage remain separate acceptance work.

## Recorded local results — November 17, 2026

- Ruby/Bundler/Jekyll/Sass build: passed; source dependency pins unchanged.
- Existing offline JavaScript tests: **9 passed**.
- Generated project paths: **40 HTML files passed**.
- Navigation: **90 route/viewport checks passed** at 320/390/768/1024/1280/1440,
  plus five-category/context switching, role-aware controls, links and helper modes.
- Existing homepage/feature acceptance: **156 route/viewport checks passed**, with
  fixed hero content/geometry, three distinct loaded photos, automatic rotation,
  published/missing tip fixtures, notices, preferences, kit and resource behaviors.
- New preferences: **8 themes at 4 widths passed**, with keyboard selection,
  persistence, custom color preview/save/contrast rejection, fonts/sizes/buttons,
  English/Spanish label persistence/reset, speech opt-in/voice/rate/pitch/volume,
  explicit selected/page reading, pause/resume/stop and unsupported-browser tests.
- Broader frontend/backend release runner: **5/10 feature versus 4/10 main**.
  Feature now passes real local profile integration as well as SCSS, request worker,
  quiz and account regression. The profile suite's final signed-out assertion was
  intentionally updated for the requested public prompt and verifies no private
  edit fields after logout. Main retains its earlier missing-risk-widget failure.
  Community tools, legacy responsive, production contract, admin security and media
  release still fail on both, with the same duplicate-selector, absent legacy
  element and review/API-origin expectations. Paired result/cause JSON is preserved.

Screenshots (unavailable/401 API fixtures, no fabricated resident data):
[desktop theme picker](111326-navigation-preferences-evidence/theme-picker-1280.png),
[mobile theme picker](111326-navigation-preferences-evidence/theme-picker-390.png),
[desktop Preferences](111326-navigation-preferences-evidence/preferences-1280.png),
[mobile Preferences](111326-navigation-preferences-evidence/preferences-390.png),
[desktop Profile](111326-navigation-preferences-evidence/profile-signed-out-1280.png),
[mobile Profile](111326-navigation-preferences-evidence/profile-signed-out-390.png),
[mobile navigation](111326-navigation-preferences-evidence/profile-mobile-navigation.png),
[desktop Home](111326-navigation-preferences-evidence/home-1280.png),
[mobile Home](111326-navigation-preferences-evidence/home-390.png).

These passes cover mocked browser contracts and disposable local integration,
not production authentication, full translation or real voice playback. Manual
screen-reader/audio review, five broader release gaps and content-owner acceptance
remain open. Full release readiness is not claimed.
