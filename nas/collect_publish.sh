#!/bin/sh
# Dedicated checkout: never run this in /volume1/btc-cvd.
set -eu
umask 077
MODE=${1:---check}
case "$MODE" in --check|--run) ;; *) echo 'Use --check or --run' >&2; exit 2 ;; esac
BTC_REPO=${BTC_REPO:-/volume1/btc-monitor}
BTC_PYTHON=${BTC_PYTHON:-/volume1/btc-cvd/venv/bin/python}
BTC_LOCK=${BTC_LOCK:-/volume1/btc-monitor-publish.lock}
export GIT_TERMINAL_PROMPT=0
# Respect the explicit key and verified known_hosts configured by the NAS task.
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes -o ConnectTimeout=15}"
export PYTHONDONTWRITEBYTECODE=1
unset GITHUB_OUTPUT GITHUB_STEP_SUMMARY
exec 9>"$BTC_LOCK"
/bin/flock -n 9 || { echo 'Another NAS collection is running; skipped.'; exit 0; }
cd "$BTC_REPO"
[ "$(git config --get remote.origin.url)" = 'git@github.com:Cravendor/btc-monitor.git' ] || {
  echo 'Unexpected origin; expected the repository-scoped SSH connection.' >&2; exit 1;
}
[ "$(git branch --show-current)" = main ] || { echo 'Checkout must be on main.' >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || {
  echo 'Checkout contains uncommitted files. Preserve and inspect them before retrying.' >&2; exit 1;
}
"$BTC_PYTHON" -c 'import sys, ssl, sqlite3; assert sys.version_info >= (3, 9), "Python 3.9+ required"; print("Python:", sys.version.split()[0])'
git ls-remote --exit-code origin refs/heads/main >/dev/null
if [ "$MODE" = --check ]; then
  echo 'Read-only connection and runtime check passed. Write permission is not yet verified.'
  exit 0
fi
# Recover any previously committed but unpushed observations before collecting again.
# On a conflict, abort the rebase; keep the local commit for manual recovery.
git fetch origin main
if ! git rebase origin/main; then
  git rebase --abort
  echo 'Upload conflict: local observations preserved. Inspect before retrying.' >&2
  exit 1
fi
# Check the exact fetched collector before it runs.
"$BTC_PYTHON" -m unittest discover -s tests
COLLECT_EXIT=0
# Read the separate journal in-place; no copy, migration or collector restart.
export BTC_CVD_DB="${BTC_CVD_DB:-/volume1/btc-cvd/trades.sqlite3}"
export BTC_CVD_BACKFILL_STORE="${BTC_CVD_BACKFILL_STORE:-/volume1/btc-cvd/backfill/candidates.sqlite3}"
export BTC_COLLECTOR_SOURCE=nas
# Failed/unfinished coverage never blocks publication of the normal market metrics.
# Cached candidates are replay-verified; a new closed interval is recovered/resumed.
if [ -f "$BTC_CVD_DB" ]; then
  "$BTC_PYTHON" -m scripts.cvd_pipeline --journal "$BTC_CVD_DB" \
    --store "$BTC_CVD_BACKFILL_STORE" || echo 'CVD coverage pending; publishing available observations.'
fi
"$BTC_PYTHON" scripts/collect.py || COLLECT_EXIT=$?
"$BTC_PYTHON" -m scripts.collector_health
# Stage only known public outputs; never the CVD database, logs or credentials.
git add -- data/latest.json data/timeframe-health.json data/collector-health.json data/history/timeframe_signals.jsonl
for year in data/[0-9][0-9][0-9][0-9]; do
  [ ! -d "$year" ] || git add -- "$year"
done
if ! git diff --cached --quiet; then
  git -c user.name='BTC NAS collector' -c user.email='btc-nas@users.noreply.github.com' commit -m 'Save NAS BTC market snapshot'
fi
# No force push: concurrent GitHub writes produce a safe failure. The commit stays local.
git push origin HEAD:main
[ "$COLLECT_EXIT" -eq 0 ] || exit "$COLLECT_EXIT"
"$BTC_PYTHON" - <<'PY'
import json
from pathlib import Path
health = json.loads(Path('data/timeframe-health.json').read_text())
if health.get('snapshot_status') != 'ok':
    raise SystemExit('Snapshot uploaded with incomplete source data; inspect source statuses')
print('NAS snapshot uploaded. Dashboard publication is a separate GitHub run.')
PY

