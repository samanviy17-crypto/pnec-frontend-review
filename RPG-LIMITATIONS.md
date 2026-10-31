# Preparedness RPG — explicit scope decision required

The wrapper is a PNEC-branded resident feature, linked from the role quiz to
/rpg/latest/. It is not a dependency of account, quiz scoring, household plans,
checklists, calendar, maps, FAQ or community APIs. It is optional to those core
workflows, but cannot honestly be described as an unrelated page while its visible
resident link remains. No wrapper, link or functionality was removed here.

## Missing implementation

The normal autostart path requires assets/js/rpg/latest/GameControl.js, absent in
both audited release and capstone sources. assets/js/GameEnginev1.5/Game.js is also
absent. The Mansion fallback exists upstream but is a classroom game core with its
own account/leaderboard integration. A bounded import trace reaches 40 module
paths: 34 existing and six missing/static placeholder references, including optional
leaderboard/pause/score/level-skip support. Copying Game.js alone cannot complete
PNEC gameplay, and optional/comment imports are not all mandatory runtime blockers.

## Recommended initial-publication decision

Explicitly defer the optional RPG from the first resident release unless its PNEC
scenario/engine implementation is supplied. This requires owner approval to remove
or disable the visible quiz link and remove the wrapper from the publication
snapshot while preserving an archive outside it. That exclusion is PROPOSED ONLY;
this snapshot retains the current feature and documents its nonfunctional engine.

If the RPG is required, supply the approved PNEC GameControl and scenario/level
modules, select one engine, trace its complete module/media dependencies, preserve
licenses, remove classroom account/leaderboard coupling and server defaults, scan
all new assets, then run isolated gameplay/mission/storage/mobile tests. Do not
copy an entire classroom game or use existing user data as fixtures. The old
repositories must remain untouched. Review-only publication must disclose this
limitation; production gameplay is not validated.
