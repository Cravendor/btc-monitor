"""CLI to evaluate a Bitget latest.json snapshot without publishing signals.

The result is an auditable provisional assessment, not a confirmed trade
signal. Time is explicitly supplied by the caller to avoid hidden clock
dependencies in historical tests.
"""
import argparse
import json
from pathlib import Path
from scripts.bitget_4h_assessment import assess_latest_4h


def evaluate_file(path, as_of):
    feed = json.loads(Path(path).read_text(encoding="utf-8"))
    return assess_latest_4h(feed, as_of)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot")
    parser.add_argument("--as-of", required=True, help="UTC timestamp with timezone")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = evaluate_file(args.snapshot, args.as_of)
    rendered = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
