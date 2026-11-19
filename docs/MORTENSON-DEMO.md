# PNEC 11/13/26 Redesign — Mortenson demonstration

Prepared November 17, 2026. Review branch:
`feature/mortenson-website-redesign-20261116`, existing [Draft PR #1](https://github.com/samanviy17-crypto/pnec-frontend-review/pull/1).
This is a **stakeholder demonstration**, not permission to merge or deploy.

Allow about 10–12 minutes. Keep a desktop window and a 390px mobile window ready.
Use only synthetic accounts and descriptions. Obtain the local review account
privately from the owner-only credentials file printed by the disposable launcher;
never paste it into presentation slides, GitHub, screenshots, or this guide.

| Order | Local URL | Suggested demonstration / expected result |
|---|---|---|
| 1 · Home and navigation | http://localhost:8766/ | Five primary categories and far-right Login. Home uses the full width with no sidebar or empty sidebar space. Show About PNEC and the four action cards. |
| 2 · Poway slideshow | http://localhost:8766/ | Leave the page for about 20 seconds with reduced motion off. Three real Poway photographs rotate behind the same heading, description, Get Prepared button and tip. Keyboard focus remains stable. Reduced motion intentionally stops animation. |
| 3 · Weekly Preparedness Tip | http://localhost:8766/#weekly-tip-heading | Tip comes from the disposable backend's real weekly API. Explain its week/source and educational label; it is not an emergency alert. Missing data has an availability message. |
| 4 · Conditional sidebars | http://localhost:8766/pages/checklist.html | Prepare gets its own destinations. Visit Resources and Community to change the sidebar; Home removes it. At mobile width use the menu, Tab, Escape and focus return. |
| 5 · OCS-style theme picker | http://localhost:8766/pages/settings.html#appearance | Select Midnight, Green or Ocean, then return to Home and reload. All eight presets persist locally. Custom colors preview before Save and reject inadequate contrast. Restore Site Default. |
| 6 · Language and audio | http://localhost:8766/pages/settings.html#language and http://localhost:8766/pages/settings.html#audio | Save Spanish and show translated navigation/preferences; editorial text remains English. Reset English. Enable speech explicitly, choose a voice, test/pause/stop, and turn it off. Audible output must be checked on the actual presentation computer. |
| 7 · Login and account | http://localhost:8766/pages/register.html#login | Sign in privately with the synthetic review account. Login becomes Account. Open My Profile and show the dashboard/Account Settings, save a synthetic bio, reload, and show Logout. Registration is also available at `#register`; it creates a resident, never an admin. |
| 8 · Preparedness tools | http://localhost:8766/pages/checklist.html | Save a clearly synthetic household plan, answer the assessment, save a synthetic Safe check-in and submit a clearly synthetic non-emergency hazard. Reload to show persistence. Signed-out visitors get login links. These forms are not emergency dispatch. |
| 9 · Community interactions | http://localhost:8766/pages/volunteer.html | Show the synthetic shift board. Resident can claim/cancel; coordinators post/manage only their assigned neighborhood. Volunteer-interest form is separate from assigning account roles. The informational SYNTHETIC community banner can be dismissed; a changed version reappears. |
| 10 · Wildfire guide | http://localhost:8766/pages/fire-safety.html | Resources sidebar and Prepare related link. Show zones 0–5, 5–30, 30–100 feet, applicable new-tree mature-drip-line 10ft and canopy-edge separation 20ft. Move the diagram sliders with arrow keys. Contrast new landscaping, existing chimney maintenance, roof recommendations and pending state rules. Open source links/verification date. |
| 11 · Limitations and feedback | http://localhost:8766/pages/profile.html | Ask Mr. Mortenson to review navigation, readability, theme names and preparedness wording. Explain the local backend compatibility repair, partial Spanish and outstanding manual accessibility/content review. End signed out. |

## Before the meeting

The frontend and disposable backend are currently running together:

- Frontend: **http://localhost:8766/**; Settings: **http://localhost:8766/pages/settings.html**.
- API: **http://localhost:8426/api/health**, **http://localhost:8426/api/ready**.
- Safety marker: **http://localhost:8426/api/local-review** reports disposable,
  synthetic-only data, blocked external providers, and two local compatibility repairs.
- Port 8425 belongs to an unrelated older service. Leave it alone. Use matching
  `localhost` hostnames for this preview and API, rather than mixing loopback names.
- Do not start a second server on an occupied port. A fresh browser context avoids
  earlier notice dismissal/theme choices. The synthetic notice expires two hours
  after acceptance testing; an empty banner after expiry is correct behavior.
- If fresh fixtures are needed, the owner can run `scripts/test-stakeholder-live.py`
  using the private credentials file. It creates synthetic role fixtures, a future
  shift and a short-lived informational notice. It never seeds production data.

If restarting from scratch, use the backend requirements in the external Python
venv, then run these in separate terminals from the feature worktree:

```sh
# Creates a new private temporary SQLite database and synthetic account.
# The flag uses existing backend routes/decorators, repairing only this local copy.
/path/to/venv/bin/python -B scripts/local-review-backend.py \
  --backend-root /path/to/pnec-backend-review --port 8426 --enable-announcements

# Tracked production configuration stays unchanged.
cat > /tmp/pnec-mortenson-local.yml <<'YAML'
local_api_port: 8426
YAML
bundle exec jekyll build --config _config.yml,/tmp/pnec-mortenson-local.yml \
  --destination /tmp/pnec-redesign-preview-8766
python3 -m http.server 8766 --bind 127.0.0.1 \
  --directory /tmp/pnec-redesign-preview-8766
```

`--resume-state <private-disposable-state-directory>` preserves an existing review
DB/account. Only an owner-private `pnec-local-review-*` directory with the expected
credentials/database is accepted. Restarting rotates the session secret: sign in
again. The launcher copies no resident database, `.env`, uploads or production
secrets; no backend checkout is edited.

## Readiness and remaining limitations

**Ready for stakeholder review:** yes, with these disclosed limitations.
**Ready for merging/production deployment:** no.

1. The unmodified backend omits announcement blueprint registration and its
   baseline migration omits the table. The local launcher explicitly repairs both
   for the demonstration. The proposed [backend patch](backend-patches/register-announcements.patch)
   passed a fresh isolated migration and HTTP role/CSRF tests, but is **not applied
   to backend main**. Backend owners must review it, reconcile any existing table,
   update version-specific acceptance tests, and approve its release separately.
2. Human VoiceOver/NVDA review, actual audible playback and presentation-device
   Safari/Firefox/Chrome checks are still needed. Engine automation is not proof
   of screen-reader usability or audible output. See the [manual checklist](MORTENSON-RELEASE-AUDIT.md#manual-acceptance-checks).
3. Spanish covers reviewed navigation/preferences labels. It does not translate
   all forms, editorial guides, user content or API messages.
4. Live weather, AI, email/reset delivery, remote publication, payments and
   production resident data are outside this synthetic environment. No purchase,
   publication, production action or real incident was submitted. Some legacy
   images depend on external sites; offline screenshots intentionally block them.
5. Content-owner approval is required for legacy claims/statistics/testimonials,
   translations, notices and fire guidance. The fire guide is not a parcel finding;
   its November 17 source check does not establish a statewide Zone 0 start date.
6. Explicit user approval is still required before any merge or deployment.

[Current screenshots and evidence](mortenson-final-review/README.md) ·
[Full release-readiness audit](MORTENSON-RELEASE-AUDIT.md) ·
[Exact changes since 3f41a99](MORTENSON-FINAL-CHANGES.md).
