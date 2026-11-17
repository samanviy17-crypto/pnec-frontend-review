# Route review inventory — November 16, 2026

Source baseline: `ce475278ba406ddb4fa39a93daafb6dd3b5f7af7`. Shared shell, tokens, notifications and appearance settings apply to every route below. Automated QA: Codex in this implementation session. The suggested teammate ownership remains in pages #5; individual owner review is pending.

| Generated route | Page | Local checks |
|---|---|---|
| `/404.html` | Page Not Found — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/donation-form/index.html` | Support PNEC — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/index.html` | Prepared neighbors. A stronger Poway. — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/about.html` | About PNEC — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/admin-blog.html` | Blog Manager — PNEC Admin — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/admin-chatbot-analytics.html` | Helper Bot Analytics — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/admin-editor.html` | Live Theme Editor — PNEC Admin — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/admin-map-align.html` | Map Alignment Tool — PNEC Admin — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/admin-map-hotspots.html` | Map Hotspot Editor — PNEC Admin — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/admin-nav.html` | Site Nav Manager — PNEC Admin — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/admin-security.html` | Security Dashboard — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/admin-volunteer.html` | Volunteer Dashboard — PNEC Admin — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/admin.html` | Admin Dashboard — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/blog-post.html` | Blog Post — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/blog.html` | Blog — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/checklist.html` | My Emergency Kit — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/community-events-and-activities.html` | Community Events — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/contact.html` | Contact PNEC — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/dashboard.html` | Community Coordination Dashboard — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/events-archive.html` | Past Events & Articles — Poway Neighborhood Emergency Corps — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/find-your-neighborhood.html` | Find Your Neighborhood — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/forgot-password.html` | Forgot Password — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/gallery.html` | Community Gallery — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/kit.html` | 72-Hour Emergency Kit Checklist — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/manage-events.html` | Manage Events — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/onboarding.html` | Welcome to PNEC — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/poway-statistics-and-information.html` | Poway Statistics and Information – Poway NEC & FSC | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/preparedness-resources.html` | Preparedness & Help — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/privacy.html` | Privacy Policy — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/profile.html` | Profile — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/programs-and-services.html` | Programs and Services — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/register.html` | Login or Create Account — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/reset-password.html` | Reset Password — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/security.html` | Security & Privacy — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/settings.html` | Appearance & Settings — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/upload.html` | Upload Media — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/pages/volunteer.html` | Volunteer with PNEC — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/role-quiz/index.html` | Find Your PNEC Role — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |
| `/rpg/latest/index.html` | Emergency Preparedness RPG — PNEC — isolated source review | 320 / 390 / 768 / 1280px, anonymous API fixtures |

Existing interaction inventory:

- `pages/checklist.html` / `assets/js/pages/community-tools.js`: household plan, quiz, check-ins, hazard reporting, local kit progress; API/account gates retained.
- `pages/kit.html` / `assets/js/pages/kit.js`, `assets/js/ui/kit-ui.js`: local checklist, explanations, progress, print/share/reset. Adds search while preserving state.
- `pages/volunteer.html`: API shifts precede role descriptions and interest form. Existing selection and submit feedback retained.
- `pages/community-events-and-activities.html`: calendar/list controls precede editorial material. Weekly content uses `/api/preparedness/weekly`.
- `pages/find-your-neighborhood.html`: interactive map and search retained.
- `pages/preparedness-resources.html`: adds action links, topic shortcuts, expandable resource guidance and library search before long reference material.
- `pages/profile.html`, account/password pages, staff/admin dashboards: existing role/authentication controls retained; shared sidebar and settings applied.
- No standalone fire or earthquake page, or interactive fire-tree source, was found in this frontend, the related backend checkout, or the related pages repository tree at `bb2d8a291337bf9bcfab782679cbf71c76d1e2b3`. Existing wildfire/earthquake resources and the events archive are retained. Exact fire-tree parity requires its actual source from the owner.

This inventory verifies page loading, shared navigation, overflow and absence of uncaught page errors with fixtures. It does not certify every authenticated workflow or substitute for individual content-owner review.
