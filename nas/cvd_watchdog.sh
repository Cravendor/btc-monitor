#!/bin/sh
# Existing DSM watchdog, with minimal execution evidence. No new schedule.
DIR=/volume1/btc-cvd
REPO=/volume1/btc-monitor/repo
RECEIPTS=/volume1/btc-monitor/task-executions-pending
STARTED_AT=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

receipt() {
    /usr/local/bin/python3.9 "$REPO/scripts/task_execution.py" watchdog "$1" \
        --root "$RECEIPTS" --started-at "$STARTED_AT" >> "$DIR/watchdog.log" 2>&1 ||
        echo "$(date -u) - Uitvoerbewijs opslaan mislukt" >> "$DIR/watchdog.log"
}

active() {
    ps -ef | grep '[b]itget_cvd_collector.py' | grep -v 'grep' >/dev/null
}

cd "$DIR" || { receipt error; exit 1; }
if active; then
    echo "$(date -u) - Collector draait" >> "$DIR/watchdog.log"
    receipt completed
    exit 0
fi

echo "$(date -u) - Collector starten" >> "$DIR/watchdog.log"
nohup /bin/flock -n "$DIR/collector.lock" \
    "$DIR/venv/bin/python" \
    "$DIR/bitget_cvd_collector.py" \
    --db "$DIR/trades.sqlite3" \
    --health "$DIR/health.json" \
    --log "$DIR/collector.log" \
    >> "$DIR/collector-start.log" 2>&1 < /dev/null &

sleep 2
if active; then
    echo "$(date -u) - Collectorproces aanwezig na startpoging" >> "$DIR/watchdog.log"
    receipt completed
    exit 0
fi
echo "$(date -u) - Geen collectorproces na startpoging" >> "$DIR/watchdog.log"
receipt error
exit 1
