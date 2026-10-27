# Reconstruct a frozen Elliott observation

The read-only `scripts.elliott_observation_restore.reconstruct` takes an available
manifest and recreates the original normalized rows and fixed candidate inventory
from the exact Git commit referenced at capture. It does not call the exchange or
rewrite the manifest. Four linked source files are loaded from that commit into a
temporary directory; their byte hashes, closed boundaries, source quality and
cross-timeframe checks must still match. The saved audit is found by its exact
content SHA-256 in that same commit and must pass the original bounded audit
eligibility checks at the observation time. The recomputed candle-row hash and
full inventory must match the manifest.

A non-available manifest is never converted into a scenario. Missing Git objects,
changed source files, ineligible/missing audit, changed anchors or model inputs,
future or malformed timestamps, and inconsistent source evidence stop the
reconstruction. The current implementations of the model and data-validation
modules must be byte-identical to those at capture. This conservative fail-closed
rule can block older records after a legitimate code change. Supporting archived,
versioned runtimes is future work; never silently evaluate old records using newer
logic. The frozen ledger's weekly evaluation boundary has also been corrected to
use Monday UTC, consistent with native weekly candles.

SHA-256 hashes expose unexpected byte changes; they are not digital signatures
and cannot independently prove who created a record or when it was observed.
An audit verifies only its bounded recent window and is not proof that historical
values never changed. Git history must remain reachable. No missing object is
replaced with current data. Tests use isolated committed fixtures; live available
manifest reconstruction remains untested until one is genuinely captured.

This is a library-only preparation: it does not schedule evaluation, reconstruct
unavailable records, generate backfilled forecasts, calculate a hit rate or claim
predictive value. Future integration needs an as-observed later-data source,
revision-aware availability, durable first-outcome records and bounded processing.
