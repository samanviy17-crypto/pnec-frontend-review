# PNEC light theme review

Preview: [http://localhost:8794/pnec-frontend-review/](http://localhost:8794/pnec-frontend-review/)

## Cause and changes

An unset site preference already selected Light in the prior implementation. The homepage still looked dark because the carousel had a full-width navy backdrop and overlay independent of the preference tokens. The checklist and role quiz had separate navy gradients. The registration backdrop and some profile and blog elements also used fixed dark styling. Helper Bot Auto followed a separate OS/media-query path, so it could appear dark while the page used Light.

Site Default remains explicitly Light, and the root sets the native color scheme to light until a dark preference resolves. A saved Dark or Use system setting remains valid. Choosing Site Default restores the default light palette, plain background and font. Reset restores the appearance defaults while retaining language and audio. Helper Bot Auto follows the site's resolved color scheme. The bot's explicit Light or Dark selection still takes precedence.

The typography and photos are in separate columns on desktop, then stack on smaller screens. The photos no longer determine the contrast of the heading or controls. The four existing homepage cards retain their Builder data, icons and links. Credits are in a keyboard-accessible disclosure below the resources. Reduced motion and the pause control remain available.

## OCS integration

Uses the vendored OCS navigation pattern, `base-grid`, `grid-card-cell`, `base-button`, `text-button`, `inline-container`, `responsive-padding`, `responsive-text`, `form-group`, and OCS spacing and radius tokens. Shared site colors feed the existing OCS custom properties. The two existing UI Builder documents still supply the homepage link cards and Preparedness Journey. The homepage photo carousel and localized appearance controls are PNEC-specific. Existing account forms and templates retain their backend contracts. Builder cloud storage and publishing were outside this local redesign.

WCAG contrast for default `#173E2A` text is 11.94:1 on white, 11.29:1 on pale green, 10.32:1 on light blue and 6.06:1 on brand green. Dark green link text is 5.80:1 on white and 5.02:1 on light blue. These measurements cover the shared palette pairs, rather than constituting a full accessibility audit.

## Homepage photo credits

- Wildfire-prevention briefing with Poway, San Diego, and Miramar firefighters at MCAS Miramar, September 2026. U.S. Marine Corps photo by Cpl. Seferino Gamez, U.S. public domain. [DVIDS source](https://www.dvidshub.net/image/9927737/mcas-miramar-conducts-prescribed-burn-preparation-americas-air-show-2026)
- Wildland firefighting exercise at Camp Pendleton, May 2025. U.S. Marine Corps photo by Cpl. Jacqueline Akamelu, U.S. public domain. [DVIDS source](https://www.dvidshub.net/image/9015708/local-fire-protection-services-camp-pendleton-marines-and-sailors-train-together-cory-iverson-training-exercise)
- Emergency-kit distribution in New Orleans, May 2006. Marvin Nauman/FEMA, U.S. public domain. [FEMA archive record](https://commons.wikimedia.org/wiki/File:FEMA_-_24466_-_Photograph_by_Marvin_Nauman_taken_on_05-21-2006_in_Louisiana.jpg)

The carousel presents these as archived preparedness images. Original November 19 images remain in the working tree.

## Verification

Chromium checked new users on a dark OS setting, saved Dark, explicit Use system setting, Site Default, reset and all eight presets at 390, 820 and 1440 pixels. It checked primary button and card colors, navigation surfaces, above-the-fold desktop cards, images, reduced motion, credits and Helper Bot. Existing preference tests also cover custom palettes. Screenshots are in `/tmp/pnec-light-review`.

The expanded Spanish catalog and language-aware speech remain in place. This pass added Spanish text for photo credits, appearance options and kit labels. The 40-route bilingual check still reports untranslated text in legacy and dynamic content.

The 40-route signed-out survey in a clean profile recorded no computed dark solid surfaces at least 400 by 150 CSS pixels at desktop width. That survey excludes CSS gradients, photo pixels and game-engine-rendered content. The admin sign-in card and RPG waiting shell now use theme tokens. The RPG retains its gameplay rendering and fullscreen framing.

## Browser follow-up on localhost:8794

A same-origin diagnostic loaded the current build in the existing Chrome profile without writing appearance preferences. It found `theme=system`, `preset=site-default`, no custom colors, and an OS dark preference. The HTML resolved to Dark, with `--pnec-surface: #172638` and `--pnec-bg: #0d1928`. The header, hero and cards computed to navy while the primary button computed to `#61CF70`. A clean Chromium profile on the same simulated dark OS resolved to Light. The root URL on port 8794 is the preview directory index, and the built site lives at `/pnec-frontend-review/`.

The compiled OCS stylesheet loads after the legacy page, fallback and card styles, then the appearance controller resolves the saved scheme and optional palette overrides. Settings now leaves the Site Default swatch unselected while System or Dark is active, even when the stored palette identifier is `site-default`. Clicking the swatch explicitly chooses Light. The existing Chrome profile's saved choice was preserved.

The follow-up regression checks computed surfaces and primary fills on the homepage and interior pages. It reproduces the saved System state and verifies that explicitly choosing Site Default survives navigation and restores the light colors.
