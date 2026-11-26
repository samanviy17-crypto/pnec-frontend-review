# November 19 PNEC website feedback

| Area | Starting state | Feature branch changes |
| --- | --- | --- |
| Brand and appearance | Partial. Presets and color checks existed. The default accent was teal and several community widgets used fixed foregrounds and backgrounds. | Brand actions use `#61CF70` with dark ink. Light-surface links use a darker green. Community panels follow the selected foreground and surface, and the three resource cards use theme-colored line icons. |
| Helper Bot | Partial. The shared widget had independent palettes, type and display controls. | The default launcher, new-chat action and outgoing message bubbles share the brand fill and dark ink. Explicit bot accent choices still apply. The bot follows the site's font preference and reads replies in the language set for the conversation. |
| Home | Partial. Three attributed Poway photos, the published tip and four action cards existed. The hero dedicated at least 620 pixels to its copy and tip. | Reframed the local photographs in a shorter hero, added the volunteer action and put the tip beside About PNEC. The existing four-card include and destinations are preserved. |
| OCS and content | Partial. Shared navigation and vendored OCS Sass were in use. The separate Builder pilot had an importable static link-card export. | Adapted the export to a three-step Preparedness Journey. The Liquid adapter renders real app routes with the configured Jekyll base path. Corrected selected resource copy and the household plan shortcut. |
| Spanish and speech | Partial. Navigation and Preferences had reviewed Spanish labels. Reading used the configured voice or document language for all text. | The speech sample follows the language preference. Page and selected-text reading follow the language marked on the content and use a compatible installed voice where available. |
| Preparedness assessment and plan | Implemented and account-backed. Both forms took a single column of labels and controls. | Paired fields in a responsive two-column layout with a full-width evacuation field. The existing assessment questions, scoring, account checks and save endpoints remain the source of truth. |
| Guided journey | Missing. Shortcuts existed without a recommended sequence. | Home and Prepare navigation link to three numbered steps that lead to the assessment, household plan and kit checklist. |

## UI Builder review

Import [the journey JSON](../_data/pnec_preparedness.json) into OCS UI Builder as a local draft. It uses the pilot's version 1 `ocs-ui-page` stack, heading and `link_cards` block types. Jekyll renders that same content through [the Liquid include](../_includes/pnec-preparedness.html). The site uses the vendored OCS `base-grid`, `grid-card-cell`, `inline-container`, `main-container`, `responsive-padding` and button patterns for layout and styling.

This integration covers static headings, text and links. Authentication, saved form values, scoring, kit progress and dynamic content depend on the existing PNEC app and its API. The linked workflow uses those routes directly. The updated JSON rendered in the local Jekyll artifact and in the hosted Builder’s Phone and Desktop previews after import into an unsigned local draft. The browser blocked outbound writes during verification. Signed-in cloud storage and publishing remain unverified.

Spanish coverage is limited to reviewed labels and the audio sample. English guides, resident data and API content retain their original language. Installed browser and operating-system voices determine whether audio can play.

## Verification

- JavaScript suite passed all 10 tests, including Helper Bot voice selection.
- Jekyll and Sass built for the GitHub project path and the isolated root-domain release.
- The isolated release suite passed all 10 checks, including accounts, role and preparedness quizzes, community tools, authorization, responsive layout and the production configuration contract. Account and save tests used a disposable local backend and synthetic data.
- Chromium passed 90 shared-navigation and 160 redesign route-and-viewport checks. Preferences passed eight themes at four widths, including fixture-based Spanish speech. The brand, hero, header geometry and all journey links also passed focused checks at 390, 768 and 1280 pixels.
- The supplied text specified the exact brand hex. Visual verification used the rendered local site because the original reference image was unavailable in the attachment.
