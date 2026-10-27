# Prospective Elliott observation manifests

This change proposes attaching manifest capture to the existing BTC multi-year
history workflow, after source checkpoints and the bounded revision audit have
been committed. No new schedule, NAS task or paid service is added.

The runner uses its actual UTC clock and checks that all four native cache files
match the bytes in the checked-out Git commit, before and after parsing. It stores
that commit, each file's SHA-256 and the current revision-audit SHA-256. For an
available manifest it also records the original as-of candidate inventory and the
hash of the exact normalized closed candle rows; the full rows can be reconstructed
from the pinned commit. This avoids copying years of candles on every run. Git
history must remain retained and reachable: loss of the referenced commit means
that observation cannot be reproduced.

Eligibility is deliberately conservative: all 1W/1D/4H/1H histories must be
complete and every linked parent-child group reconciled with zero skipped groups.
The current bounded revision audit must be at most ten minutes old, unchanged,
current for every scale and match the four committed file hashes. Its limited
last-two-candle coverage does not prove all older data were never revised. Open
candles and future source observations are rejected. When a gate fails, each
scale records `unavailable` with reason and source states, without inventing an
inventory or neutral result. The current 4H/1H source conflict consequently
blocks all linked scales; this is a conservative policy, not a claim every
individual candle is wrong.

For each timeframe and closed boundary, the first unavailable and first
available records are separate immutable files. A subsequent successful retry
can therefore preserve recovery without rewriting the original failure. Repeated
runs verify the existing file hash and do not replace it. Concurrent file writes
use atomic create-only links; the existing workflow concurrency group serializes
its runs. A push rejected due to another writer leaves this workflow failed; its
newly created current manifests are uploaded as a 30-day artifact for recovery,
not silently claimed as durable Git records. A real rejected-push recovery has
not been induced or validated.

This change captures observations only. It does not automatically evaluate
future outcomes, store fake past predictions, calculate probabilities, create a
dashboard view or certify Elliott counts. A separate integration must reconstruct
exact source snapshots and preserve later evaluation/availability and source
revision evidence without rewriting prior versions. Current capture is not active
until reviewed merge and an actual eligible workflow execution; a local dry run
showed all four scales unavailable on the conflicting/stale input.
