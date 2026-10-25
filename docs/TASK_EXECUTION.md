# Minimal task execution evidence

task_execution_protocol_version: 1

This protocol permits minimal public receipts from actual executions, including
runs with no market alert. No extra scheduled tasks or user notifications.
A receipt proves completion of an attempted check, not live process state,
source quality, market bias or notification delivery. Missing evidence is unknown,
not stopped. Never reconstruct past runs or publish private task identifiers.

## Immutable receipt

Create exactly one new UTF-8 JSON file on main with the GitHub create_file tool:
`data/task-executions/SOURCE/TASK/YYYYMMDDTHHMMSSZ.json`.
Use the actual UTC completion time for the filename. Precisely these six fields:

- `schema_version`: integer 1.
- `source`: `chatgpt` or `nas`.
- `task`: an allowed identity below.
- `started_at`: actual aware ISO8601 start time, or null if not recorded.
- `finished_at`: actual aware ISO8601 completion time.
- `outcome`: `completed` or `error`.

`completed` means the check actually finished, even if market data was missing
or there was no alert. Use `error` only for an observed failed execution. No
report text, prompts, free error details, secrets or account/conversation/task IDs.
If the run aborts before writing, no receipt exists; do not fabricate one.

Allowed ChatGPT identities: `4h-warning`, `psychology`, `breaking-risk`,
`quality-improvement`. Allowed NAS identities: `watchdog`, `storage`, `startup`.
VIX and other tasks are not connected by this change.

Before writing read the exact destination. Identical content means already
submitted; differing content must not be replaced. After an uncertain response,
read the same path before retrying. A missing protocol or write failure must not
interrupt normal analysis or create an extra market alert. No other files may
be changed by the automation. Do not merge PRs or change schedules from a run.

## Status interpretation

Latest receipt wins, including errors. Invalid newer evidence must not expose
an older success. Future timestamps, timezone-free times, unexpected fields and
identity/path mismatches are rejected. Explicit errors stay red until a later
valid receipt. Completed checks expire to amber after: 4H monitor 6h, psychology
30h, breaking news 3h, Quality & Improvement 35 days, watchdog 45m (5m checks transported by 30m publication), storage 36h.
These are tolerance windows, not proof of exact schedule execution or uptime.
Startup runs remain grey with their recorded time: boot events have no periodic
freshness expectation. No receipts means grey. Browser expiry also removes green.

Receipts trigger the existing Pages workflow; they create no new workflow or
polling task. GitHub may queue publication; receipt submission does not prove
live deployment. Historical receipts remain available for the existing QI review;
no uptime percentage can be inferred from one current card.

## NAS integration is prepared, not installed

The reader and `python -m scripts.task_execution TASK OUTCOME` writer are ready.
The writer uses actual completion time and exclusive file creation. Optional
`--started-at` must be a time recorded by the actual task. `--root` permits an
external receipt directory. It does not start/restart a process, publish or alter
DSM scripts. Do not paste a generic replacement over an existing DSM task.

Before connecting the existing watchdog/storage/start scripts, obtain their
current full task names and contents. Preserve commands, exit handling, locks,
Python environments and recorder. Record success only after the original check
succeeds, error only after its failure, and publish receipts through an explicitly
reviewed existing upload path. This change does not install these hooks or add
receipts to the NAS publisher's Git staging list. Local receipts alone are not
visible remotely. Keep those cards grey until actual published evidence exists.

## Watchdog connection prepared from the actual DSM script

nas/cvd_watchdog.sh preserves the supplied /volume1/btc-cvd recorder command,
venv, DB, health/log paths and flock. It checks process presence after a two-second
start grace. This is process-presence evidence only, not proof of new trades,
coverage or future survival. Receipt write failure is logged but does not restart
or stop an already-present collector.

DSM receipts go to /volume1/btc-monitor/task-executions-pending, outside the Git
checkout /volume1/btc-monitor/repo. The publisher imports strict NAS-only receipts
after collection, stages them with existing public outputs, and removes identical
spool files only after successful push. Invalid/conflicting receipts remain local;
no raw logs or arbitrary fields are imported. A failed push retains both local
commit and spool. Existing concurrent-writer recovery rules still apply.

Installation: merge the implementation, let the existing publisher successfully
update its checkout, then replace only the existing BTC CVD Watchdog task body
with /bin/sh /volume1/btc-monitor/repo/nas/cvd_watchdog.sh. Retain its existing
user and five-minute schedule. Do not create another task or run the recorder
manually. Script must be readable and the existing user must be able to write
the external spool. Inspect actual next-run evidence and publication afterwards.
Storage/startup tasks still need their actual current scripts.

## Storage check connection prepared from the supplied DSM body

nas/cvd_storage_check.sh keeps the actual ls/du/date report at
/volume1/btc-cvd/storage-check.txt. Only its six-field storage receipt goes into
the external spool for the existing uploader. It fails on missing database
files, failed size inspection or failed report redirection, even if the final
date command succeeds. Receipt-write failure is nonzero and leaves the report.
It does not modify the database or restart the recorder. Successful completion
does not verify SQLite integrity, free capacity, disk health or full collection.
The existing 36-hour storage freshness tolerance is unchanged; actual DSM task
name/schedule has not been supplied and must be checked before interpreting
periodicity. The size reported by du is total btc-cvd directory usage, not just
the database. Raw sizes, paths, command errors and report text are not published.

After merge and confirmed NAS code update, preserve the existing storage task's
user and schedule and replace only its body with:
/bin/sh /volume1/btc-monitor/repo/nas/cvd_storage_check.sh
No new DSM task. Verify a real next execution, uploaded receipt and live card.
The startup task remains unconnected until its actual body is supplied.
