# PNEC localization, imagery and OCS review

Preview: [http://localhost:8794/pnec-frontend-review/](http://localhost:8794/pnec-frontend-review/)

## Localization coverage and release gaps

The Jekyll data catalog is `_data/pnec_es.json`. The shared layout loads the catalog and runtime from `assets/js/ui/locale.js`. The preference controller persists the locale and the runtime sets the document language. Explicit catalog bindings accept stable keys and parameters. The static migration scan uses normalized English source text as compatibility keys for existing markup and preserves text nodes, form values and link destinations. New dynamic components should use namespaced keys and explicit bindings. The scan is restricted to rendered templates and explicitly passed, app-owned UI subtrees. There is no external translation service or request.

This pass covers common menus, accessible names in the shared shell, homepage actions, the Builder journey, preferences, assessment questions and known recommendations, household fields, the checklist items, role quiz scenarios and choices, and selected community, account and Helper Bot labels. Some outputs still use the original implementation. The audit confirms route delivery and locale metadata and flags visible English leaf text. It does not exhaustively exercise every dialog, protected role, native form error, CMS payload, or JavaScript branch.

Outstanding first-party work includes full editorial translation of About, archived events, fire safety, security and privacy, volunteer and donation copy, the RPG, account and password workflows, staff/admin controls, some checklist explanatory text, validation messages, chatbot suggestions, and dynamic status and error output. The [route inventory](/tmp/pnec-localization-untranslated.json) includes raw visible text candidates by route. Candidates also include proper names and third-party excerpts. Mixed-content nodes, attributes and some later-rendered branches require additional review.

The translations for ten known assessment prompts and recommendations mirror the API's published English wording. Answers, scoring, account requests and backend validation remain on the existing contract. New or revised API-authored guidance may remain in English until a reviewed entry is available. Resident names, private notes, plans, hazard narratives, chat history, third-party documents and staff-entered events/tips retain their source text. Voice playback honors marked source languages and stops with install guidance when a required compatible voice is unavailable. Browser voices and native validation behavior depend on the device. Existing Tagalog resource and Helper Bot options remain available.

### Proposed privacy-reviewed workflow

Have PNEC approve an English/Spanish field model for owned CMS records and immutable message IDs for structured API responses. Store reviewed translations alongside the original with the review date and source language. Have a fluent local reviewer check emergency, evacuation, health, and legal guidance before publishing. Treat user-submitted plans, account data, incident reports and conversations as private. Keep them outside any translation vendor workflow by default. Before considering translation of private text, require a privacy review of purpose, consent, redaction, access controls, retention and vendor terms. Mark the source language for fallbacks and label it in the interface.

## Default theme and OCS

Reviewed the OCS checkout at `0579a0eb849a1284e99e7e4a77829cff65a68322`, including `_sass/open-coding/mixins/README.md`, the grid, buttons, container, forms and modal mixins, `_sass/open-coding/navbar.scss`, `_layouts/dashboard.html`, `assets/js/pages/dashboard/preferences.js`, and the hosted UI Builder. PNEC already vendors the grid, button, container, navigation and spacing foundations. The additional vendored `_sass/vendor/ocs/_forms.scss` comes from `_sass/open-coding/mixins/_forms.scss` at that revision (Apache-2.0). Preparedness fields now use OCS `form-group` with a visible keyboard-focus outline. The default site palette is applied via PNEC variables bridged to the same OCS surface, accent, text and border properties. New/reset preferences default to light, and saved system/dark/custom selections continue to resolve through the preference controller.

The Builder exports are `_data/pnec_preparedness.json` and `_data/pnec_home_cards.json`. The homepage still uses the existing four-card OCS layout and icons. It now reads titles, descriptions and links from its importable Builder document. Both exports use the real heading and `link_cards` blocks. Phone and Desktop previews were checked in the hosted editor as unsigned local drafts with outbound writes blocked. Cloud storage, publishing, and OCS account persistence were outside the check. The assessment and household plan are linked by the Builder and kept in the PNEC application for identity, validation, private data and save/reload. The same applies to the map, checklist, quiz scoring, CMS tools, and admin workflows. Legacy Elementor, custom map, auth, distinct modal, RPG, and staff components still need route-specific migration analysis. The toolkit source does not establish drop-in compatibility for those workflows.

## Image sources

The three source pages identify these photographs as U.S. public domain. The local assets are resized and JPEG-compressed. The carousel labels them as archives, links each credit, and retains reduced-motion handling and the pause control. The photos are decorative backgrounds with equivalent context in the linked captions.

- `assets/images/hero-miramar.jpg` shows the Miramar brush-fire response in San Diego. Credit Lance Cpl. Jackson Rush, U.S. Marine Corps. [DVIDS source and rights](https://www.dvidshub.net/image/8830580/mcas-miramar-flightline-brush-fire-extinguished)
- `assets/images/hero-rancho.jpg` shows archival Rancho Bernardo wildfire conditions from 2007. Credit Sgt. Michael Amicy, California National Guard. [DVIDS source and rights](https://www.dvidshub.net/image/69830/fires-rancho-bernardo-california)
- `assets/images/hero-fema.jpg` shows an emergency kit being handed out at a 2006 family preparedness event in New Orleans. Credit Marvin Nauman/FEMA. [FEMA archive record and rights](https://commons.wikimedia.org/wiki/File:FEMA_-_24466_-_Photograph_by_Marvin_Nauman_taken_on_05-21-2006_in_Louisiana.jpg)

Remaining approvals for a release include PNEC editorial acceptance of the imagery, fluent review of Spanish public-safety copy, and privacy review of any workflow for translating CMS or resident content.

## Route and component audit

All routes below already inherit the PNEC shell. The route-specific components are the remaining candidates for OCS reuse.

| Built routes | OCS adoption and retained work |
| --- | --- |
| Home, Preparedness & Help, Poway Statistics and Information, About, Fire Safety, Programs and Services, and 404 | Shared navigation and OCS grid/cards are suitable for static content. Home and Preparedness Journey use Builder exports. Remaining imported editorial markup, filtering and fire-safety diagrams need content-by-content adaptation. |
| Checklist, Emergency Kit, Role Quiz and Preparedness RPG | Use OCS form grouping and grids around preparedness actions. Native checkboxes, progress rendering, role scoring, focus management and RPG game state remain PNEC-specific. |
| Community Events, Event Archive, Volunteer, Donation, Gallery, Blog, Blog Post, Neighborhood Map, and Contact | OCS card and button styles can replace equivalent presentation. Preserve calendar and map interactions, media, signed-up state and submission contracts. No OCS backend is needed for these. |
| Profile, Settings, Dashboard, Register, Forgot Password, Reset Password, Onboarding, Privacy, and Security | Preferences already adopt the OCS swatch structure. Auth layout and form fields are candidates for OCS presentation mixins while retaining PNEC credentials and role gates. Policy prose requires separate editorial review. |
| Admin, Blog Manager, Helper Analytics, Theme Editor, Map Alignment, Map Hotspots, Admin Navigation, Security Dashboard, Volunteer Manager, Manage Events, and Upload | Use OCS layout, form and modal presentation after role-specific interaction and focus tests. Retain app-specific permission checks, editors, analytics, map placement and upload contracts. |

## Verification

JavaScript passed 10 tests. The project-path and isolated root-domain Jekyll/Sass builds passed. The isolated release suite passed 10 checks, including responsive, account, role quiz, community tools, authorization, and contract coverage. The community-tools test reopened a saved plan and assessment in Spanish and checked the original meeting-point value and answers with a disposable backend. Navigation passed 90 route/viewport checks, and redesign passed 160. Preferences passed eight presets across four viewport widths, including dark and custom overrides and unsupported speech. The localization test opened 40 routes in each language and checked switching, translated selections and page speech, late-loaded voices, incompatible voices, reload, long content and absence of autoplay in a browser fixture. Representative home, journey and settings layouts were checked at 390 and 1280 pixels in both locales. The Spanish page audit recorded 551 distinct visible source-text candidates, including recurring names and third-party copy. The count covers the tested states only.
