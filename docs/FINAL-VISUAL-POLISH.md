# PNEC final visual polish

[Local preview](http://localhost:8794/pnec-frontend-review/)

## Changes

- Retained the split hero and the three credited public-domain photographs. Refined heading line height, spacing, and alignment. Replaced the text-link treatment with a labeled, keyboard-operable pause/resume button and a visual state icon. The same rotation interval, reduced-motion preference, and archive credits remain.
- Kept the Helper Bot launcher in the homepage layout and removed automatic opening. The dialog and its existing behavior remain available on request. Interior pages keep the floating launcher.
- Refined the four Builder-backed action cards and the Preparedness Journey with consistent row sizing, spacing, and theme-aware hover and focus surfaces. Removed a fixed white hover background from shared cards and community tools. The pale green, light blue, green accent, and dark green text remain the default, with saved preferences and all eight presets retained.
- The weekly card starts with a static English/Spanish water-storage tip, including when JavaScript or the API is unavailable. A valid published API response replaces it with the published tip and date when supplied. Missing, failed, blank, or malformed responses retain the fallback. The fallback is sourced from FEMA and labeled as general guidance. This is a source review, and PNEC editorial approval remains separate. [FEMA emergency kit guidance](https://www.fema.gov/print/pdf/node/503732)

## OCS reuse

The shared navigation and contextual sidebar continue to use the vendored OCS navigation pattern. The visual changes reuse `base-grid`, `grid-card-cell`, `base-button`, `text-button`, `inline-container`, `main-container`, `responsive-padding`, `responsive-text`, and the spacing/radius tokens. Community form grouping retains the genuine `form-group` mixin. The appearance controls retain the OCS swatch structure. Homepage actions and the Journey continue using the existing checked-in UI Builder exports. No new Builder component API is required.

The carousel, static-to-published tip transition, and Helper Bot dialog remain PNEC-specific because they depend on this site's behavior and API. Account authorization, assessments, household plans, staff controls, quiz scoring, and the translation and speech controllers remain on the existing PNEC implementation. No backend changes were made. Existing untranslated legacy and dynamic content remains outside this visual pass.

## Files changed in this pass

- `_data/pnec_es.json`
- `_includes/chatbot/chatbot-launcher.html`
- `_includes/chatbot/chatbot-widget.html`
- `_includes/home-carousel.html`
- `_includes/weekly-preparedness-tip.html`
- `_sass/_ocs-pnec.scss`
- `_sass/_redesign-hero.scss`
- `assets/css/home-actions.scss`
- `assets/js/chatbot/index.js`
- `assets/js/pages/home-carousel.js`
- `docs/FINAL-VISUAL-POLISH.md`
- `scripts/test-light-theme.py`
- `scripts/test-mortenson-redesign.py`

## Verification

- Jekyll/Sass built the project-path preview and isolated root artifact. JavaScript and the isolated release suite each passed 10 tests/checks.
- Chromium passed 90 navigation and 160 redesign route/viewport checks. The redesign regression exercises keyboard rotation controls, reduced motion, the inline bot launcher, and published, empty, malformed, blank, and failed tip responses.
- Computed-color checks passed for the homepage and interior surfaces across all eight presets at 390, 820, and 1440 pixels. The preferences suite also passed dark/system, custom palette, persistence, and browser speech checks. The bilingual suite opened all 40 routes in both languages.
- Axe reported zero violations in 103 signed-out checks and 24 signed-in checks. The signed-in run used a disposable loopback resident account. Axe marked rules incomplete in 91 signed-out checks. Manual assistive-technology, audible speech, and color checks for image/gradient cases remain outside this audit.
