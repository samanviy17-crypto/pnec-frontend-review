# PNEC and OCS UI Builder integration

Local PNEC preview: [http://localhost:8794/pnec-frontend-review/](http://localhost:8794/pnec-frontend-review/). Editor: [OCS UI Builder](https://pages.opencodingsociety.com/ui-builder/).

## Component ownership

| Export | Builder blocks | What PNEC renders and owns |
| --- | --- | --- |
| [Preparedness Journey](../_data/pnec_preparedness.json) | One column, Heading, Link cards | The Liquid adapter renders the heading and the three ordered links to the assessment, household plan and kit. It validates the canonical origin and applies Jekyll's base path. |
| [Homepage actions](../_data/pnec_home_cards.json) | One column, Heading, Link cards | The homepage reads the four titles, descriptions and destinations from the export. PNEC provides the existing four icons and responsive card layout. The icons currently follow slot order. |
| [Preparedness Assessment](../_data/pnec_assessment.json) | One column, Heading, Key points, Link cards | The first heading and subtitle feed the existing assessment section. The key points demonstrate a synthetic question and answer in the Builder. The PNEC app fetches actual questions, preserves answer IDs, validates selections, and submits to the existing scoring API. |
| [Household Emergency Plan](../_data/pnec_household_plan.json) | One column, Heading, Key points, Link cards | The first heading and subtitle feed the existing household section. The key points show fictional field examples. The PNEC app renders the OCS-styled form and keeps authentication, validation, private values, saving and reload in the existing account flow. |

The live form grouping continues to use the vendored OCS `form-group`, `base-grid` and `text-button` patterns with the site's appearance tokens. Builder examples are excluded from the HTML data bridge. The hosted registry has no native form block. Link cards hand off to PNEC rather than displaying a public input form or sending resident information to Builder. The integration does not change APIs, scoring, authorization, account storage, or resident data handling.

## Edit and export

1. Open **My pages → Import JSON** and select the component export. Work on a draft. Avoid using names, addresses or other real household data in the Builder.
2. Select the block in **Outline**, open **Settings** if the inspector is closed, and edit the heading, key points, or cards. Keep the first Heading in the first section for the two form presentations.
3. Inspect **Phone** and **Desktop**. Confirm order, card text and the canonical HTTPS PNEC destinations with the correct anchors. Preserve the four homepage slots unless the PNEC icon mapping is updated in the same change.
4. Use **More → Export JSON → Download**. Review the resulting file before replacing the source JSON on a local branch. Check that block types, ordering, approved destinations and first-heading placement are preserved.
5. Update `_data/pnec_es.json` alongside any changed text that is rendered on PNEC. Run the local preview and inspect both languages and appearance modes. Keep PNEC's API tests in the review for either form.

## What was verified

All four files imported and exported in the hosted editor. Phone and Desktop previews showed the expected card order and link URLs. No external writes were permitted in the test browser. The hosted Spring-backed editor could open imported drafts but reported an unsaved draft when its remote write was blocked. Signed-in hosted saving, collaboration and publishing were not verified.

The edit/save/reload/export test used the same hosted editor code with its own `LocalPageStore` selected through a browser-only config override. Each document's heading was edited in Spanish, saved only in that isolated browser, reloaded, and downloaded as JSON. The exported Spanish heading and original ordered link URLs matched. No hosted configuration or repository file was changed for that override.

Spanish heading characters render and round-trip in Builder. The registry does not expose a bilingual switch or per-page PNEC palette in these exports. The hosted editor preview uses its OCS theme. The full English/Spanish switch and exact green, white and light-blue palette were verified on the PNEC site, including Spanish screenshots of the two live forms with synthetic API data. The disposable release suite exercises real local account validation, scoring and save/reload behavior separately.

## Handoff for Samarth

- Agree on who maintains the four source JSON files and who reviews English/Spanish edits. Keep the Builder export and the translation catalog in the same review.
- Decide if the homepage should move from slot-based icons to an explicit semantic mapping before allowing reordered cards.
- Decide if Builder needs a portable brand or bilingual option. Until then, use the PNEC preview to approve palette and language behavior.
- If hosted draft persistence is needed, verify it in an authorized OCS workspace with synthetic content. Keep publishing out of the review.
- If editable form layouts are needed in Builder later, evaluate a PNEC-owned component adapter that preserves existing endpoints, field IDs, auth and validation. Keep private account data outside the Builder document and preview.
