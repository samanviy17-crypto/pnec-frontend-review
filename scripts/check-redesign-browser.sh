#!/usr/bin/env bash
set -euo pipefail
site_dir="$1"
evidence_dir="$2"
preview_dir="$(mktemp -d)"
ln -s "$site_dir" "$preview_dir/pnec-frontend-review"
python3 -m http.server 8765 --bind 127.0.0.1 --directory "$preview_dir" > "$preview_dir/server.log" 2>&1 &
preview_pid=$!
trap 'kill "$preview_pid" 2>/dev/null || true; rm -rf "$preview_dir"' EXIT
python3 - <<'PY'
import time, urllib.request
for attempt in range(50):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8765/pnec-frontend-review/', timeout=1) as response:
            assert response.status == 200
        break
    except OSError:
        time.sleep(.1)
else:
    raise SystemExit('Preview failed to start')
PY
python3 scripts/test-navigation-redesign.py --base-url http://127.0.0.1:8765/pnec-frontend-review/ --output-dir "$evidence_dir"
