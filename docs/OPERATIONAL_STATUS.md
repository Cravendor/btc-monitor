# Operational status page

`btc-status.html` is a read-only task/status view, linked near the top of the
overview. `scripts/operational_status.py` builds its sanitized local evidence
JSON and copies the HTML/CSS/module assets during the existing Pages workflow.
There is no new service, paid API, NAS task, credential or process-control button.

## What each colour establishes

- Green: recent uploaded NAS evidence, recent journal trades **at that NAS
  assessment**, a recent successful GitHub run, or an explicitly running workflow.
- Amber: an old/missing expected result, partial measurement, queued/cancelled
  workflow or expired evidence. Staleness never proves a stopped NAS process.
- Red: an explicit failed measurement/run or disabled GitHub workflow. The label
  names that fact; it does not turn it into a claim that the whole system stopped.
- Grey: unavailable, malformed, future-dated or unconnected evidence. Diagnostic
  task inventory and old chat confirmations are not live runtime observations.

NAS output uses the first NAS record in the newest-first feed, even if it failed.
A newer GitHub reserve result cannot impersonate a NAS upload. At 45 minutes the
NAS upload proof expires. For each CVD market, a journal trade must be no more
than five minutes old relative to that NAS assessment, and the NAS assessment
must still be within 45 minutes. Closed-interval backfill success alone does not
establish that the current recorder is alive. Parent and market identity must be
Bitget BTCUSDT with spot/futures kept separate.

The existing public collector-health result is separate: it checks stored-market
freshness from NAS or reserve. It does not establish that the NAS or CVD process
is running, nor that every historical half-hour slot is present. DSM watchdog,
storage/start tasks and ChatGPT automations have no connected execution heartbeat
in this release and are explicitly grey. To show actual stopped/running DSM
states later requires a narrowly sanitized source, not guessing from uploads.

## Live updates and API limits

The same-origin sanitized JSON refreshes every 60 seconds; the browser clock
expires old green proof every 30 seconds even without a new deployment.
GitHub workflow/runs endpoints are requested without authentication on open and
manual refresh, at most once per 30 seconds. There is no repeating GitHub API
poll. Free unauthenticated API limits, network failures and invalid replies make
the workflow cards unknown; cached green is not silently reused.

Workflow state distinguishes an explicitly running job, its latest completed
outcome, queue/cancellation, and disabled configuration. Only matching main runs
are considered; a later failure is never hidden behind an older success. The
latest 100 repository runs bound the request; a task absent from that window is
unknown. Health/4H-history expect evidence within 90 minutes, daily history within
28 hours, Pages within two hours. These are operational grace windows, not timing
guarantees for GitHub scheduling. On-demand/event-driven successes become grey
after seven days, rather than claiming their schedules stopped.

Output is allowlisted summaries, names and timestamps. It excludes raw database
content, local paths, process IDs, private task/conversation IDs and NAS logs.
The page cannot restart, stop, enable or modify anything. Raw provider status
text is not inserted as HTML; cards use textContent and fixed repository links.

## Validation and current checkpoint

378 Python tests and five Node tests pass locally. Tests cover stale/missing/
future/wrong-market proof, reserve/NAS separation, an original newer failure,
independent journal recency, disabled/running/cancelled workflows, client-only
expiry, API-shape failure and exclusion of private runtime fields. Read-only
home/status generation succeeds. Node is required only in GitHub UI validation;
the NAS continues using Python 3.9 and does not need Node.

Independent live evidence collected in this phase: PR #67 Pages run 40138890905
succeeded and the Dutch zone label was observed after a browser refresh. The
NAS subsequently uploaded both its preserved 00:32 Amsterdam record and a fresh
00:40 record (2026-10-24T22:40:36.804304+00:00), with status=ok and
cycle_anchor_review.status=ready / activation=draft. Both journal markets had
recent trades. This proves the original draft-review producer ran; macroanchors
remain inactive. A commit-specific workflow helper returned an empty list despite
successful Pages runs: use the public repository Actions runs endpoint as a
cross-check before claiming no workflow was created.

This status page is implemented in the accompanying change. Merge, public
deployment, actual browser API access and mobile visual QA remain separate
checks. An old green screenshot cannot establish current status.

## Execution evidence checkpoint — 25 October 2026

Prepared a strict minimal task receipt protocol in [TASK_EXECUTION.md](TASK_EXECUTION.md),
reader/writer in scripts/task_execution.py and status-page integration. Each
connected ChatGPT monitor/QI task gets its own card. The newest receipt controls
status, including errors or invalid evidence; stale success expires. Startup
receipts do not prove a running process. Existing Pages builds on receipt pushes.
No new scheduled task, market alert, DSM script change or fabricated receipt.

The actual automation service was read this session: the three BTC monitors and
Quality & Improvement already contain protocol-gated receipt instructions; QI
also includes operational failures/recovery in its existing review. Schedules
were not changed. Protocol was not yet on main when checked, so public execution
is not yet proven. VIX is outside this connection. No private automation IDs or
prompts are included here.

Next: merge/publish this change, then inspect real new receipts and live cards.
NAS watchdog/storage/start hooks require the actual existing DSM script contents
and task names, followed by reviewed staging/publication integration. Reader and
writer support are prepared only; those tasks remain unconnected until then.
