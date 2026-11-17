#!/usr/bin/env bash
set -euo pipefail
site_dir="$1"
evidence_dir="$2"
preview_dir="$(mktemp -d)"
ln -s "$site_dir" "$preview_dir/pnec-frontend-review"
# An ephemeral loopback port allows independent worktrees/CI runs to coexist.
python3 - "$preview_dir" > "$preview_dir/server.log" 2>&1 <<'PY' &
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
root = Path(sys.argv[1])
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
(root / 'port').write_text(str(server.server_port))
server.serve_forever()
PY
preview_pid=$!
trap 'kill "$preview_pid" 2>/dev/null || true; wait "$preview_pid" 2>/dev/null || true; rm -rf "$preview_dir"' EXIT
python3 - "$preview_dir" <<'PY'
from pathlib import Path
import sys, time, urllib.request
for attempt in range(50):
    try:
        port = (Path(sys.argv[1]) / 'port').read_text()
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/pnec-frontend-review/', timeout=1) as response:
            assert response.status == 200
        break
    except OSError:
        time.sleep(.1)
else:
    raise SystemExit('Preview failed to start')
PY
preview_port="$(cat "$preview_dir/port")"
preview_url="http://127.0.0.1:$preview_port/pnec-frontend-review/"
python3 scripts/test-navigation-redesign.py --base-url "$preview_url" --output-dir "$evidence_dir"
python3 scripts/test-mortenson-redesign.py --base-url "$preview_url" --site "$site_dir" --output-dir "$evidence_dir"
python3 scripts/test-profile-preferences.py --base-url "$preview_url" --output-dir "$evidence_dir"
