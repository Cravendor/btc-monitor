#!/bin/sh
# Existing DSM storage report with minimal completion evidence; no new schedule.
DIR=${BTC_CVD_DIR:-/volume1/btc-cvd}
REPO=${BTC_MONITOR_REPO:-/volume1/btc-monitor/repo}
RECEIPTS=${BTC_TASK_RECEIPTS:-/volume1/btc-monitor/task-executions-pending}
PYTHON=${BTC_RECEIPT_PYTHON:-/usr/local/bin/python3.9}
STARTED_AT=$(date -u '+%Y-%m-%dT%H:%M:%SZ') || exit 1
RESULT=0
{
  echo "=== DATABASEBESTANDEN ==="
  ls -lh "$DIR"/trades.sqlite3* || RESULT=1
  echo ""
  echo "=== TOTALE DATABASEGROOTTE ==="
  du -sh "$DIR" || RESULT=1
  echo ""
  echo "=== TIJDSTEMPEL ==="
  date || RESULT=1
} > "$DIR/storage-check.txt" 2>&1 || RESULT=1

OUTCOME=completed
[ "$RESULT" -eq 0 ] || OUTCOME=error
"$PYTHON" "$REPO/scripts/task_execution.py" storage "$OUTCOME" \
  --root "$RECEIPTS" --started-at "$STARTED_AT" || {
    echo 'Opslagcontrole: uitvoerbewijs opslaan mislukt.' >&2
    exit 1
  }
exit "$RESULT"
