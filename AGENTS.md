# Start here — BTC monitor project

Before changing code, schedules, NAS tasks or interpreting project state:

1. Read [docs/HANDOVER.md](docs/HANDOVER.md) and
   [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).
2. Read [docs/DECISIONS.md](docs/DECISIONS.md) for accepted rules and superseded
   approaches. Follow the user's latest instruction over older documents.
3. Inspect the actual checkout: `git status -sb`, current commit, origin/main,
   open PRs and relevant Actions runs. Existing local changes/worktrees may be
   earlier agent work; preserve them. No reset/clean/force-push to make work easy.
4. Read task-specific documents linked from HANDOVER. Check original JSON data
   and model versions before claiming a feature, data source, deployment or
   automatic storage is working. An open PR is not a deployed change.
5. Use this context to continue the next unfinished step. Do not ask the user
   to repeat already documented choices or recreate known NAS/ChatGPT tasks.
   A missing detail should be researched first; explicitly label unresolved facts.

## Nonnegotiable project constraints

- Budget EUR 0. Public APIs and existing public GitHub standard runners only;
  no paid services, trials, subscriptions, credentials or trading permissions.
- Primary analysis market: Bitget BTCUSDT USDT-FUTURES, USDT. Other sources and
  USD spot references must remain labeled and separate.
- Missing/error/null is unavailable, never zero, neutral, success or old data
  silently carried forward. Use closed source candles and aware timestamps.
- General market context only: no private portfolio/trades, position tracking,
  automatic orders, simulated fills or fixed personal TP percentages.
- Preserve original snapshots/scenarios/interpretations and version changes.
  Engineering correctness and predictive usefulness are separate questions.
- Protect the existing NAS CVD journal, runtime, locks, watchdog and startup
  tasks. Never infer that snapshot failure means the trade recorder is offline.
- Before suggesting a NAS task, consult the task inventory in HANDOVER.
  User often operates via iPhone/DSM; avoid requiring a Mac or SSH by default.
- Do not publish private chats, task/conversation IDs, account details,
  credentials, raw CVD databases or NAS logs into this public repository.
- Do not infer current schedule state from an old Markdown file. Read the
  automation service/workflow configuration when scheduling is relevant.

## Required handoff maintenance

After EVERY executed task, update docs/HANDOVER.md and docs/PROJECT_STATUS.md
before reporting completion, in the same change or immediately after an external
result is observed. Update docs/DECISIONS.md when accepted rules change.
This includes task outcomes without a code change. Keep the current resume
section authoritative and explicitly supersede stale open/blocked checkpoints. Record what is implemented, merged, deployed and
actually observed separately; include evidence pointers, remaining blockers,
validation and the next concrete step. Note open PRs by number and recheck them
at the next session. Do not describe future activation as already operational.

Run checks appropriate to the change. For executable changes the existing CI
runs `python -m unittest discover -s tests -p 'test_*.py'` on Python 3.9.14 and
3.11 plus read-only dashboard generation. Documentation-only edits need link,
consistency and diff checks; do not add tests mirroring prose.
