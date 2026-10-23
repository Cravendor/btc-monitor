# NAS collection and GitHub publication

This installs the periodic market collector alongside the existing continuous CVD
collector. It does not modify `/volume1/btc-cvd`, its database, watchdog, boot task
or storage monitor. Set BTC_PYTHON to the separate Python 3.9 interpreter; the runner's legacy default
points to the CVD venv and must be overridden on this NAS. The preflight verifies
Python 3.9+ before any collection.
No Python packages, subscriptions or servers are installed by this script.

## Installation, one step at a time

1. Verify Git is available on the NAS (`git --version`) and check the existing
   interpreter (`/volume1/btc-cvd/venv/bin/python --version`). If either fails, stop
   and report the output; do not change the working CVD environment.
2. As `tony`, configure a dedicated SSH key for this repository. Add only its
   **public** key under `Cravendor/btc-monitor → Settings → Deploy keys`, with
   **Allow write access**. Keep the private key on the NAS, outside the checkout.
   Do not paste private keys or tokens into chat, a task script or the repository.
   Verify GitHub's host key against its official published fingerprints before
   accepting it: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints
3. On the verified DS415+ installation, use Python 3.9 separately from the CVD
   venv (which uses Python 3.8). Create a shared folder `btc-monitor` on Volume 1
   and give `tony` read/write access. Keep keys and temporary files outside the
   checkout. Export the following in each DSM task before using Git or the runner:

   ```sh
   export PATH="/var/packages/Git/target/bin:$PATH"
   export BTC_PYTHON=/usr/local/bin/python3.9
   export BTC_REPO=/volume1/btc-monitor/repo
   export BTC_LOCK=/volume1/btc-monitor/publish.lock
   export TMPDIR=/volume1/btc-monitor/tmp
   mkdir -p "$TMPDIR"
   chmod 700 "$TMPDIR"
   export GIT_SSH_COMMAND="ssh -i /volume1/btc-monitor/keys/github_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/volume1/btc-monitor/keys/known_hosts -o ConnectTimeout=15"
   ```

   The key and verified host key file must already exist. The runner preserves
   this explicit SSH configuration. `TMPDIR` avoids executing test fixtures on
   Synology's restricted `/tmp`; it changes neither mount flags nor CVD files.

   Clone a separate checkout as `tony` (only if it does not already exist):

   ```sh
   git clone git@github.com:Cravendor/btc-monitor.git "$BTC_REPO"
   /bin/sh "$BTC_REPO/nas/collect_publish.sh" --check
   ```

   `--check` makes no GitHub changes and does not collect market data. It checks
   the interpreter, branch, clean checkout, exact origin and noninteractive read
   access. It creates a local lock file; write access is verified only by a real
   upload. Ensure `tony` can write the checkout and lock file.
4. Run once manually, then inspect the dated snapshot, source statuses, history,
   `data/collector-health.json`, and the Pages workflow for that commit:

   ```sh
   /bin/sh "$BTC_REPO/nas/collect_publish.sh" --run
   ```

5. Only after that succeeds, create a DSM Task Scheduler **Scheduled Task →
   User-defined script**, user `tony`, daily, every 30 minutes (00:00
   through 23:30 Europe/Amsterdam), using the `--run` command above. Enable saved output results
   and failure notifications if already configured. Do not replace the CVD tasks.
6. Confirm at least two scheduled NAS runs and their dashboard publications.
   The periodic GitHub market collector is now manual-only: its cron, code-push
   trigger and archive-completion trigger are removed. The separate 4H archive
   and freshness watchdog keep their schedules until their replacements
   are verified. The NAS writes freshness together with each snapshot. Concurrent
   archive/watchdog writes can still reject a push; preserve local data and inspect
   conflicts rather than overwriting remote observations.

## Failure behavior and scope

A lock prevents overlapping NAS runs. The dedicated checkout must be clean; the
script never resets, cleans, force-pushes or discards stored observations. At run
start, a rebase first incorporates remote changes and any previously unpushed
local commit. A conflict aborts the rebase and preserves the local commit. A
push rejection or connection loss also preserves the commit for the next run.
Inspect repeated conflicts rather than deleting local observations. The origin
is fixed to the intended repository, with no incoming connection to the NAS.

Unit tests run against the fetched code before collection. Source errors are
saved and uploaded before the final completeness check fails. Failure before
snapshot creation must be investigated in saved task output; a recent archive
row alone does not prove valid source data. A push with the repository SSH key
can trigger the existing Pages push workflow; confirm its successful completion
rather than assuming upload means publication.

The migration covers market snapshots, the signal archive and optional read-only
CVD journal observations. The separate 4H context archive task is not migrated.
Only the GitHub market collector's automatic triggers are removed by this cutover.
Existing coverage gaps stay gaps.


## Cutover evidence and rollback (23 October 2026)

NAS commits 94c207b (12:00 UTC / 14:00 Europe/Amsterdam) and 794295f
(12:30 UTC / 14:30 Europe/Amsterdam) uploaded snapshots with all ten metric
statuses ok. Pages runs 39950121220 and 39953831222 succeeded. These two observed
uploads align with the configured schedule; they do not prove future availability.
The earlier manual test c21d0a0 is not counted as a scheduled upload.

The GitHub BTC market snapshots workflow remains runnable from Actions → Run
workflow for manual recovery. Its job also requires workflow_dispatch and a
public repository. A code push or completion of the 4H archive must not collect.
Pages push/workflow triggers and CI tests remain unchanged. The GitHub freshness
watchdog now has a gated reserve: only scheduled/manual checks may collect when
stored data are stale/missing. Workflow-completion and code-push checks remain
report-only. The main BTC market snapshots workflow itself is still manual-only.
PR #38's proposed GitHub watchdog collector recovery is superseded by the NAS
migration and should not be merged into this arrangement.

After merging, verify a subsequent NAS snapshot and Pages deployment. Do not
start a manual collector merely to prove the automatic trigger has stopped.
If NAS collection fails, inspect saved task output and retain local pending
commits. A manual GitHub run is a temporary recovery option; restoring periodic
GitHub triggers requires an explicit reviewed rollback. Verified CVD coverage and the 4H
context archive migration remain separate work.



## Read-only CVD journal observations

`nas/collect_publish.sh --run` sets `BTC_CVD_DB` to
`/volume1/btc-cvd/trades.sqlite3` unless explicitly overridden. After merging,
the existing NAS task pulls the code and includes the observations on its next
normal run; no task-script change, dependency installation or collector restart
is needed. User `tony` needs existing read access to the journal and WAL.
`--check` still checks runtime/repository access, not CVD availability.

The exporter opens the original database with SQLite `mode=ro`, query-only mode
and one read transaction. It never invokes `cvd_store.connect`, creates a missing
database, edits gaps, changes the schema, or stages the journal or raw trades.
It exports aggregates of the last fully closed UTC four-hour interval.

CVD is an optional separate status, not part of the ten market metrics or their
final completeness check. A missing/incompatible journal is recorded as missing
without stopping market collection. A successful market task therefore does not
prove CVD validity. In the new snapshot, inspect `cvd_4h.markets` and the dashboard
CVD cards: observed delta, trade count, overlap counts and last stored trade time.
No observations is null, not zero. Old snapshots remain unchanged.

The uploaded legacy collector/store never establishes full coverage or repairs
gaps. Consequently `cvd_4h.value` is null and `coverage_verified` is always false,
even when an interval has no recorded gaps. Observed deltas must not be used as
validated orderflow, cumulative CVD or evidence confirming a bullish/bearish bias.
See [CVD.md](CVD.md) for the remaining coverage/backfill work.



## Automatic GitHub reserve for missing or stale stored snapshots

The NAS remains primary. `scripts/watchdog_recovery.py` runs in the existing
public-repository `BTC collector health check` workflow on minute 13/43 UTC,
manual checks, and the existing report-only push/workflow-completion triggers.
Only `schedule`/`workflow_dispatch` may recover. It uses the existing 3600-second
freshness threshold and archive timestamp validation: this checks presence of
stored measurements, not that every metric was valid or the NAS is physically
offline. Future/malformed archive timestamps do not keep the reserve idle.

The job first fetches and fast-forwards a clean, disposable checkout of trusted
main, recomputes health, and skips market collection when current. For recovery it
runs the full tests, checks upstream again, then invokes the ordinary collector.
It explicitly removes BTC_CVD_DB and tags the snapshot collection_source as
github_fallback. CVD stays not_collected/null; no NAS journal, trade backfill,
inbound connection or continuous CVD takeover is involved. All normal source
validation and regional API restrictions remain in force.

After a recovery attempt, the job recomputes health and saves the attempt outcome
under recovery before marking stale data, failed tests or incomplete collection
as a failed job. Valid partial output is uploaded before failure is reported.
The existing Pages workflow_run trigger publishes successful and failed health
runs; a GITHUB_TOKEN push alone is not assumed to start another workflow. Push and
workflow-completion events never start recovery, preventing retry chains.

The watchdog, manual GitHub collector and 4H archive share btc-market-collector
concurrency. This serializes GitHub writers, not the NAS. Upstream is checked again
before publication: fresh observations from a restored NAS take precedence and
local reserve output is skipped. If upstream changed but remains stale, the job
fails and the next check starts from a fresh checkout. A final race can still
reject a normal push; there is no force-push, rebase of generated views, reset or
deletion of remote observations. NAS pending commits remain local on rejection;
inspect them if its existing outer fast-forward pull then refuses to proceed.
GitHub job-local output from a rejected/skipped publication is not claimed as
saved data and disappears with the disposable runner. Exactly-once collection
and uninterrupted service are not guaranteed.

Successful recovery refreshes the normal archive, so further checks skip until
data become stale again. Recovery therefore does not promise half-hour snapshots
during a long outage; it runs on the next executed check after the threshold.
When the NAS resumes, its next successful upload makes the check current again.
Both the NAS and fallback use additive collection_source metadata. The main page
shows NAS or GitHub-reserve; older records without provenance stay unknown.

The existing Synology task needs no script change. The next NAS pull picks up its
source tag. Keep the task enabled and preserve the CVD boot/watchdog tasks. The
old closed PR #38 remains superseded; this reserve is integrated with the verified
NAS publication path and includes explicit upstream-race and failure tests.
Runtime stays on standard public GitHub runners with the existing contents:write
permission and 5-minute timeout. No paid services or new credentials are enabled.
