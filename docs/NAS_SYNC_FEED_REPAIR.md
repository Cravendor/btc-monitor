# One-off uptake of the reviewed feed synchronization fix

Use only AFTER the feed fix has been merged. The old synchronization code cannot
merge its own update because it crashes while comparing feed timestamps. Ordinary
publisher retries alone do not resolve that.

Use the existing manual/disabled **BTC Git Diagnose** DSM task, user tony. Do not
create another scheduled task. Preserve its original script before editing.
The agent supplies the pinned reviewed commit below after PR creation/merge.
This step synchronizes pending public observations; it does not collect or push,
restart CVD, change its database/runtime, or alter the normal publisher task.

```sh
#!/bin/sh
set -eu
umask 077
export PATH="/var/packages/Git/target/bin:$PATH"
export BTC_PYTHON=/usr/local/bin/python3.9
export BTC_REPO=/volume1/btc-monitor/repo
export BTC_LOCK=/volume1/btc-monitor/publish.lock
export TMPDIR=/volume1/btc-monitor/tmp
export GIT_TERMINAL_PROMPT=0
export PYTHONDONTWRITEBYTECODE=1
export GIT_SSH_COMMAND="ssh -i /volume1/btc-monitor/keys/github_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/volume1/btc-monitor/keys/known_hosts -o ConnectTimeout=15"
BTC_REPAIR_COMMIT=REVIEWED_FIX_COMMIT_PENDING
mkdir -p "$TMPDIR"
chmod 700 "$TMPDIR"
exec 9>"$BTC_LOCK"
/bin/flock -n 9 || { echo 'Publisher active; repair not started.'; exit 1; }
cd "$BTC_REPO"
[ "$(git config --get remote.origin.url)" = 'git@github.com:Cravendor/btc-monitor.git' ]
git fetch origin main
git merge-base --is-ancestor "$BTC_REPAIR_COMMIT" origin/main
repair_script=$(mktemp "$TMPDIR/sync-publish-repair.XXXXXX")
trap 'rm -f "$repair_script"' 0
git show "$BTC_REPAIR_COMMIT:nas/sync_publish.py" > "$repair_script"
"$BTC_PYTHON" "$repair_script" --repo "$BTC_REPO" --backup-dir /volume1/btc-monitor/publish-backups
echo 'Guarded synchronization completed. Normal publisher may now resume.'
```

The helper independently requires clean main, correct origin, no active Git
operation and only recognized pending public observations. It preserves/merges
history, verifies immutable blobs and creates/verifies an external bundle before
the divergent merge. Unknown local changes fail for investigation; do not remove
them. Keep the diagnostic task disabled for scheduling afterwards.

After successful synchronization, allow one existing normal publisher execution
(or manually run that existing task once if needed). Inspect its full finished
result and original published snapshot, followed by commit-specific Pages. A
new GitHub fallback is not NAS acceptance, and upload success does not prove full
CVD coverage. Retain any private diagnostic output outside the public repository.
