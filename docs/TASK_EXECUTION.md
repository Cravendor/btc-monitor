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
30h, breaking news 3h, Quality & Improvement 35 days, watchdog 15m, storage 36h.
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
