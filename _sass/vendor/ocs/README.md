# OCS Sass source

Original mixins copied (trailing whitespace normalized) from the locally available OCS-based repository
https://github.com/samanviy17-crypto/pages at commit
7dc1e9915d0f506bdbd24c287d8b164cfce9bc6f:
- _sass/open-coding/mixins/_variables.scss
- _sass/open-coding/mixins/_grid.scss
- _sass/open-coding/mixins/_buttons.scss

Upstream: https://github.com/Open-Coding-Society/pages
License: Apache-2.0 (included).

home-actions.scss imports these actual sources and uses base-grid,
grid-card-cell, base-button, responsive-padding, and responsive-text.
The scoped PNEC extension supplies white/navy/teal theme variables, icon/text
placement, a larger radius, a subtle shadow, explicit 4/2/1 breakpoints, and
overrides the toolkit's hover transform to prevent movement. The whole anchor
is the control; the decorative arrow is not a nested button.

The redesign additionally vendors the unmodified _container.scss mixins.
_navigation.scss contains an exact selector excerpt from open-coding/navbar.scss;
the course-specific glass/toast/DM behavior is omitted. Its import is scoped to
#pnec-site-header. See docs/REDESIGN.md for the template adaptation and minimal
disclosure extension. ocs-pnec.scss uses base-grid, grid-card-cell, text-button,
inline-container, main-container and the original spacing tokens.
