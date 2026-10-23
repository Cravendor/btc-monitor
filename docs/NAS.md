# NAS collection and GitHub publication

This installs the periodic market collector alongside the existing continuous CVD
collector. It does not modify `/volume1/btc-cvd`, its database, watchdog, boot task
or storage monitor. The default interpreter reuses its existing venv; the check
requires Python 3.9+ and verifies the actual version before any collection.
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
   User-defined script**, user `tony`, daily, every 30 minutes (for example 00:07
   through 23:37), using the `--run` command above. Enable saved output results
   and failure notifications if already configured. Do not replace the CVD tasks.
6. Confirm at least two scheduled NAS runs and their dashboard publications.
   Then remove the corresponding GitHub collector/archive schedules and watchdog
   recovery in a separate reviewed change. Leave the current GitHub schedules
   enabled during setup. The brief overlap can cause a rejected push; it cannot
   authorize overwriting remote data.

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

This first migration step covers market snapshots and the signal archive. It
neither exports SQLite CVD data nor moves the separate 4H context archive task.
Those require follow-up integration after NAS publication has been verified.
No cron schedules are disabled by this change. Existing coverage gaps stay gaps.
