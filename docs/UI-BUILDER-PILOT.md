# PNEC UI Builder pilot

The Preparedness & Help page now renders three links from an importable OCS UI Builder document. Residents can move from the resource library to the existing emergency kit checklist, volunteer role quiz, and neighborhood map. The card section uses the builder’s heading and link-card structure, a named navigation landmark, and PNEC-local styling. Jekyll converts links for the canonical PNEC origin to site-relative URLs so the same document works in Builder previews and in GitHub project-path builds.

[Team issue #52](https://github.com/samanviy17-crypto/team-portfolio/issues/52) · [Original exports, guides, screenshots and prototype](https://gist.github.com/svaka2000/70a43cfe7975e280f163718f171680a0) · [OCS UI Builder](https://pages.opencodingsociety.com/ui-builder/)

## Review of the four exports

Each JSON imported into the deployed builder in an isolated browser session, opened Code, and rendered at 1280 px and 375 px without document-level horizontal overflow. Outbound writes were blocked for the review. The builder kept the imports as local drafts, so this checks the current importer and renderer. Signed-in cloud storage, collaborative editing, publishing, and published visibility still need verification if the team adopts them. All four exports contain the same menu destinations under `/ui-builder/view/?page=`, with addresses `pnec`, `pnec-about`, `pnec-programs`, and `pnec-get-involved`.

| Export | Findings |
| --- | --- |
| Home | The alt text describes the lake photo and the action cards point to useful tasks. The kit checklist and role quiz URLs target the current capstone host and returned HTTP 200. The demo repeats the hero and links already present on the home page. The link-card group lacks a landmark name in the builder preview. |
| About | Clear history, mission, and board sections. The 2011 date agrees with PNEC’s About page. The board table has a caption and column headers and fits the tested phone viewport. PNEC must approve the names and roles before any publication. The current home already links to the capstone About page. |
| Programs and Events | Program summaries follow PNEC’s descriptions and the image has descriptive alt text. The table has column headers but no caption. Confirm recurring schedules and venues with PNEC before publishing. Keep event dates in the existing event source so annual summaries cannot be mistaken for confirmed upcoming dates. |
| Get Involved | The map link and role quiz provide useful entry points. Repeated email calls to action and three role cards with empty descriptions reduce clarity. The link-card landmark is unnamed. The demo's email action reaches the organization's contact address and does not exercise the app’s volunteer interest form. |

The four-link menu wraps on phone and is rendered as a group of buttons without a named navigation landmark or a current-page indicator. The branded prototype also needs mobile menu behavior and a strategy for link contrast, page titles, and visitor theme overrides. If OCS adds reusable pieces, a labeled link-card group and a shared responsive navigation block would address observed gaps. Programs and event promotion cards are a second candidate for a small pilot once content ownership is agreed. Login, saved checklist progress, quiz logic, volunteer submissions, events data, the neighborhood map, and CMS editing stay with PNEC’s existing app.

## Edit the links

1. Open the [source JSON](../_data/pnec_preparedness.json) and download it.
2. Open the UI Builder and select **My pages** → **Import JSON**. Edit the heading or link cards, then check **Preview** and **Code** at phone and desktop widths.
3. Export the page JSON from the builder. Keep the document to one stack with a heading followed by link cards. Use full URLs on `https://powaynec.opencodingsociety.com` with paths that already exist in PNEC. Copy the updated heading and card settings into the checked-in export and review the build. The Liquid adapter is scoped to this section shape and origin.
4. Use a branch and PR for updates. PNEC approval is required before publishing organizational demo pages, especially the About board roster. The original guide also describes OCS teacher approval for public access.

## Volunteer integration

PNEC’s official About page dates the organization to 2011. The roughly 100 CERT volunteers are the City of Poway’s team. The volunteer page removes unsupported headline stats and training claims, links directly to the City’s CERT program, and preserves the existing `cert_volunteer` form value for questions and compatibility. [PNEC About](https://powaynec.com/about/) · [City of Poway CERT](https://poway.org/436/Community-Emergency-Response-Team-CERT)

On November 18, the legacy Beasts host returned HTTP 502 for health and the volunteer route. The current capstone frontend’s configured API returned HTTP 200 for health and a successful CORS preflight for the live frontend origin. An ordinary GET to the POST-only submission endpoint returned 405. The pilot keeps the configured endpoint and request format. On network failure, a timeout, or an unconfirmed response, it retains the entries and shows the official contact link. Only an HTTP success with JSON `ok: true` clears the form. The current API checks were read-only. End-to-end production submission and coordinator handling need an authorized synthetic test. [Current PNEC frontend](https://powaynec.opencodingsociety.com/) · [Current API health](https://powaynec-api.opencodingsociety.com/api/health) · [PNEC contact](https://powaynec.com/contact/)

## Verification

The frontend CI browser suite checks the three actual Jekyll routes and keyboard focus across its six viewport widths, along with existing navigation and account display. It intercepts synthetic volunteer requests and checks input validation, network failure, HTML 502, invalid success JSON, and confirmed success. CI also runs the offline JavaScript suite and the Jekyll project-path checks.
