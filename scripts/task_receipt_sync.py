"""Copy only validated public NAS receipts from an external spool; acknowledge after push."""
import argparse
import json
from pathlib import Path
from scripts.task_execution import validate


def receipts(root):
    root = Path(root)
    for task in ('watchdog', 'storage', 'startup'):
        folder = root / 'nas' / task
        if folder.is_symlink() or (root / 'nas').is_symlink():
            continue
        for path in folder.glob('*.json'):
            try:
                if path.is_symlink() or not path.is_file() or path.stat().st_size > 2048:
                    raise ValueError('not a minimal receipt')
                raw = path.read_bytes()
                relative = path.relative_to(root)
                validate(json.loads(raw), relative)
                yield path, relative, raw
            except (ValueError, TypeError, OSError, OverflowError):
                print('Skipped invalid NAS receipt; original retained locally.')


def sync(root, destination, acknowledge=False):
    copied = 0
    for path, relative, raw in receipts(root):
        target = Path(destination) / relative
        try:
            if target.is_symlink():
                raise ValueError('symlink target')
            if target.exists():
                if target.read_bytes() != raw:
                    raise ValueError('immutable receipt conflict')
            elif acknowledge:
                continue
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as out:
                    out.write(raw)
                copied += 1
            if acknowledge:
                path.unlink()
        except (OSError, ValueError):
            print('NAS receipt not synchronized; original retained locally.')
    return copied


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root')
    parser.add_argument('destination')
    parser.add_argument('--acknowledge', action='store_true', help='Only after a successful Git push')
    args = parser.parse_args()
    sync(args.root, args.destination, args.acknowledge)
