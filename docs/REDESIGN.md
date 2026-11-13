# PNEC OCS redesign

## Source and scope

Frontend review repository only. Backend code and infrastructure are unchanged.
The current user request explicitly selects this repository; historical issue #2
is a reference, not authorization to change its separate production repository.

## Why the navigation shifted

The homepage rendered poway-live-body.html, several editorial routes were
standalone WordPress documents with their own headers, regular pages selected
between poway-header.html and nav/navbar.html, and password pages used another
layout. poway-page-enhancements.js moved navigation after DOM readiness, added
logos and galleries, while pnec-nav-patch.js rewrote the cloned menu. Different
CSS bundles, font rules, title bands and content/scrollbar widths further changed
geometry. These were different implementations, rather than a single active-tab
styling issue.

All application routes now use pnec-base.html and ocs-header.html. The password
layout delegates to the same base. Editorial pages retain their main content,
map, calendar and feature markup, and discard duplicated document chrome.
Blog and blog-post now render their own content rather than the homepage clone.
The old snapshot files remain in source for historical reference but are not
loaded by the application layout.

The header has a fixed 80px height and position; body padding reserves its space.
Local Arial avoids font-download shifts. Links use the same weight and dimensions
for every state, with an inset active indicator. A fixed brand and account slot,
stable scrollbar gutter, scoped styling, and identical includes keep positions
consistent. The review warning and announcement content remain below the fixed
header. The helper is opened explicitly and has a lower stacking order.

## Genuine OCS foundation

Sources are vendored under _sass/vendor/ocs with Apache-2.0 license. Source:
local OCS-based samanviy17-crypto/pages checkout, revision
7dc1e9915d0f506bdbd24c287d8b164cfce9bc6f; upstream Open-Coding-Society/pages.

Imports:
- vendor/ocs/variables: original spacing, radius, breakpoint, font-size and
  transition tokens, responsive-text and responsive-padding mixins.
- vendor/ocs/grid: original base-grid and grid-card-cell mixins.
- vendor/ocs/buttons: original base-button and text-button mixins.
- vendor/ocs/container: original main-container and inline-container mixins.
- vendor/ocs/navigation: documented exact selector excerpt from
  open-coding/navbar.scss, imported inside the shared header.

ocs-header.html adapts the real OCS _includes/themes/minima/header.html structure:
site-header, wrapper, site-title, site-nav, trigger and page-link, relative_url
links, separate login access, and mobile nav-trigger. OCS's source header is flat
and uses minima.nav_pages; it does not provide nested accessible disclosures.
PNEC uses its own scoped data file and native buttons to extend that structure.
The OCS course login endpoint is not used because PNEC has its own working auth.

Minimal PNEC extensions: palette, image hero, icon/text composition, fixed header
dimensions, disclosure placement, account slot, mobile breakpoints, focus rings,
and removal of the toolkit hover lift. These are extensions, not invented OCS
APIs. The rest of the site retains existing feature-specific form CSS. Editorial
page-builder markup uses OCS containers/cards/spacing through scoped Sass.
The former global _polish.scss import is replaced because it added blue link
effects, gradients, background effects, and transforms conflicting with the new
design. Legacy files are retained but are no longer loaded to mutate the menu.

## Routes and access

| Menu | Existing destinations | Access |
| --- | --- | --- |
| Home | / | Public |
| Prepare | /pages/checklist.html, #preparedness-quiz, /pages/kit.html, /role-quiz/ | Guides public; saved household/quiz data requires login |
| Community | /pages/volunteer.html, /pages/community-events-and-activities.html, /pages/checklist.html#hazard-reporting, /pages/find-your-neighborhood.html, /pages/gallery.html, /pages/blog.html, /donation-form/ | Information public; claiming shifts/reporting hazards requires login |
| Resources | /pages/preparedness-resources.html, /pages/programs-and-services.html, #poway-risk-context, /pages/events-archive.html, /pages/security.html | Public |
| About | /pages/about.html, /pages/contact.html | Public |
| Account | /pages/register.html, /pages/profile.html, /pages/upload.html, /pages/manage-events.html, /pages/dashboard.html, /pages/admin.html, /pages/admin-editor.html, logout | Existing role-gated account access |

Additional destinations from the existing _data/pnec_nav.yml manager are appended
inside Resources if not already mapped. The manager remains usable for additional
resource destinations; the new five-category structure is in ocs_navigation.yml.
All internal menu/card paths use relative_url. Existing permalinks are retained.
The statistics route remains a compatibility redirect into the resource library.

## Homepage and page identity

The four action cards are preserved in home-action-cards.html, including their
exact text, icons and existing destinations. They immediately follow the hero.
Their OCS grid has equal rows and 4/2/1 columns, whole-card links, and no transform
on hover/focus. The quiz points to the actual preparedness assessment, not the
separate role quiz. Both deep-linked tool sections keep their existing behavior.

The homepage adds a local Poway image, clear actions, About PNEC, a static weekly
tip (not a claimed API feed), and links to events/resources/neighborhoods.
It does not invent upcoming events. The events page retains its real calendar
and list API views with existing empty/error states.

Editorial content is preserved: About has story/history and mission sections;
Programs has service panels; Preparedness has an organized resource library;
Neighborhood retains its interactive map; Events keeps calendar and activity
content; Contact retains its external contact form. Volunteer shifts, household
planning, hazard reporting, account and saving controls retain existing scripts.
Empty builder columns and spacers are removed; the oversized Volunteer hero and
checklist padding are reduced. Content-specific feature CSS remains where needed.

## Verification

Local tools were installed outside the checkout under /tmp/pnec-tools. The local
Jekyll build used a temporary Gemfile with base64, bigdecimal and the GFM parser
for compatibility with the host's Ruby 4. Source Gemfile pins are unchanged.
GitHub Actions uses the existing Ruby 3.3 setup.

Commands:
- npm test (temporary Node 24 on PATH).
- BUNDLE_GEMFILE=/tmp/pnec-tools/Gemfile bundle exec jekyll build
  --destination /tmp/pnec-redesign-site --config _config.yml,_config.pages.yml.
- python3 scripts/check-pages-paths.py --site /tmp/pnec-redesign-site.
- python scripts/test-navigation-redesign.py --base-url
  http://127.0.0.1:8765/pnec-frontend-review/ --output-dir /tmp/pnec-evidence.
- git diff --check.

The browser regression checks 15 routes at 1440, 1280, 1024, 768, 390 and 320px,
header and desktop link bounding boxes, actual menu link transitions, dropdown
click/keyboard/ArrowDown/Space/Escape/outside dismissal, mobile opening/closing,
synthetic cached-account visibility and resident role gating, 4/2/1 equal-height
cards, unchanged hover/focus boxes, card destinations, console errors, and
horizontal overflow. Repeatable tests mock API reads and external resources;
they do not claim to exercise live backend authentication.

A separate live API smoke check used only a synthetic example.test account:
health/readiness and CORS, register, /auth/me, household plan PATCH/GET, clearing
the synthetic plan, quiz/tasks/events/hazards reads, logout and fresh login.
No hazard report or volunteer task was created. The synthetic account remains
in disposable review storage; no unsupported deletion endpoint was invented.

Both CI and Pages build workflows execute the browser regression before
publication. Deployment status and live browser results are reported separately
after their runs; a successful local build is not a deployment claim.

## Remaining external limitations

Existing review warnings remain in place. Storage is disposable, email/AI/game
features retain their existing limitations. External editorial images and the
third-party contact form depend on their original hosts. Navigation's flat legacy
editor manages extra Resources links; editing category structure uses the new YAML.

Local result: all existing JavaScript test files passed; Jekyll compiled in the
temporary Ruby bundle; generated project-path checks passed across 39 HTML files.
The browser matrix passed all 90 route/viewport checks with zero page errors,
including all six responsive widths and the interaction/account checks described
above. Screenshots and machine-readable results are in /tmp/pnec-evidence.

Vendored source changes are limited to trailing-whitespace normalization; mixin behavior is unchanged.
