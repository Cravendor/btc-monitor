# DS415+ Bitget collector: first controlled smoke test

Prerequisites verified on NAS: DSM 7.1.1, Python 3.8.12 at
`/usr/bin/python3`, virtualenv `/volume1/btc-cvd/venv`,
websocket-client 1.8.0. Public SPOT and USDT-FUTURES subscriptions
previously succeeded.

## Preparation

Download **both** repository files from this branch into the same NAS folder:

- `scripts/bitget_cvd_collector.py` -> `/volume1/btc-cvd/bitget_cvd_collector.py`
- `scripts/cvd_store.py` -> `/volume1/btc-cvd/cvd_store.py`

Do not use the GitHub main branch; this code is in draft PR #3.

## Bounded smoke test (not 24/7 yet)

In DSM Task Scheduler create a manual-only user-defined script.
Run as an account that can write to the shared folder.
This starts the collector for approximately two minutes and stops it,
without requiring a publicly exposed SSH service.

```sh
cd /volume1/btc-cvd || exit 1
/volume1/btc-cvd/venv/bin/python bitget_cvd_collector.py \
  --db /volume1/btc-cvd/trades.sqlite3 \
  --health /volume1/btc-cvd/health.json \
  --log /volume1/btc-cvd/collector.log &
PID=$!
sleep 120
kill -TERM "$PID" 2>/dev/null
wait "$PID" 2>/dev/null
/volume1/btc-cvd/venv/bin/python -c "import json; d=json.load(open('/volume1/btc-cvd/health.json')); print(json.dumps(d, indent=2))" \
  > /volume1/btc-cvd/smoke-result.txt 2>&1
```

Inspect `smoke-result.txt` and `collector.log` in File Station.
Expected health output has both markets, trade counts and
`coverage_verified: false`. It must NOT show official validated CVD.
If there is a failure, stop and inspect the log before scheduling.

## Limitations before continuous operation

The journal records unverified observations only. A connection or successful
snapshot does not prove no missed trades. Bitget aggressor-side semantics and
size unit must be checked against current exchange documentation before
labeling signed volumes as official CVD. Initial snapshot data may overlap
updates; trade IDs deduplicate. Database growth, disk capacity, concurrent
writes and restart behavior need extended tests. The collector has no safe
remote GitHub upload configured and must not be exposed to the internet.
Do not add an always-on task until these checks pass.
