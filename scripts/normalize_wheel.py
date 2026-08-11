#!/usr/bin/env python3
"""Canonicalize platform-only ZIP metadata in one built wheel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from normshift.audit.wheel_normalize import (  # noqa: E402
    WheelNormalizationError,
    assert_canonical_wheel_file,
    normalize_wheel_file,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        help="New canonical wheel path; required unless --check is used",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate canonical bytes without modifying the wheel",
    )
    args = parser.parse_args(argv)
    if args.check and args.output is not None:
        parser.error("--check and --output are mutually exclusive")
    if not args.check and args.output is None:
        parser.error("--output is required when canonicalizing a wheel")
    try:
        result = (
            assert_canonical_wheel_file(args.wheel)
            if args.check
            else normalize_wheel_file(args.wheel, args.output)
        )
    except (OSError, WheelNormalizationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "changed": result.changed,
                "fields_changed": result.fields_changed,
                "input_sha256": result.input_sha256,
                "member_count": result.member_count,
                "output_sha256": result.output_sha256,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
