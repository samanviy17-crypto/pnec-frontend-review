# Verification — November 17, 2026

Jekyll/Sass root and project-path builds passed; generated path checks: 41 HTML files. JavaScript: 9/9. Browser fixtures: 90 navigation checks; 160 homepage/feature checks; eight themes at four widths; fire/login/offline/empty-data checks at four widths. These fixtures do not establish production readiness.

Actual isolated backend: login/logout, all four database-backed forms, persistence, cookie/CORS/CSRF and resident authorization passed on both localhost and 127.0.0.1. Only synthetic data was used. Relevant backend pytest: **86 passed**, 3045 deprecation warnings. Backend source was copied to a temporary directory before testing.

Broader runner: feature **5/10**, clean main ce47527 **4/10**. Same five failures: community-tools duplicate `.community-tools` locator; legacy responsive expects an obsolete navigation element; production-contract expects a different pages configuration; admin-security and media-release use a mismatched API origin (media ultimately times out). Paired raw results/logs are retained here. Main additionally fails its old profile-widget expectation; feature Profile passes. These failures remain unresolved, rather than being presented as acceptance success.

Manual screen-reader/audible speech, full translation coverage, parcel-specific fire-code interpretation and content-owner approval remain review work. No merge, deployment, production-data access or main modification was performed.
