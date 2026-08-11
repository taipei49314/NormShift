#!/usr/bin/env python3
"""Run the exact frozen M1/M2 metric scorer from this source tree."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from normshift.acceptance.scorer import (  # noqa: E402
    AcceptanceScoringError,
    score_acceptance,
)
from normshift.evidence.hashing import canonical_json_bytes  # noqa: E402
from normshift.io_safety import (  # noqa: E402
    PathSafetyError,
    assert_outputs_safe,
    atomic_write_bytes,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Recompute frozen per-class M1/M2 metrics (never grants external PASS)."
    )
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--scorer-manifest", type=Path, required=True)
    parser.add_argument(
        "--scorer-manifest-sha256",
        required=True,
        help="Independently approved lowercase SHA-256 trust anchor (not an ambient sidecar).",
    )
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--required-phase", choices=("M1", "M2", "ALL"), required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Dedicated directory outside source/evidence inputs; output name is fixed.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    inputs = [args.policy, args.gold, args.predictions, args.scorer_manifest]
    try:
        output_root = args.output_root
        if output_root.is_symlink() or not output_root.is_dir():
            raise PathSafetyError("--output-root must be an existing non-symlink directory")
        existing = list(output_root.iterdir())
        output = output_root / "acceptance-result.json"
        if any(path != output for path in existing):
            raise PathSafetyError(
                "--output-root must be empty except for the replaceable fixed output"
            )
        assert_outputs_safe(
            inputs=[*inputs, args.source_root],
            outputs=[output],
            labels=["acceptance-result.json"],
        )
        result = score_acceptance(
            policy_path=args.policy,
            gold_path=args.gold,
            predictions_path=args.predictions,
            scorer_manifest_path=args.scorer_manifest,
            expected_scorer_manifest_sha256=args.scorer_manifest_sha256,
            source_root=args.source_root,
        )
        atomic_write_bytes(output, canonical_json_bytes(result.model_dump(mode="json")))
    except (AcceptanceScoringError, PathSafetyError, OSError) as exc:
        message = str(exc).replace("\r", " ").replace("\n", " ")[:2000]
        print(f"acceptance scoring failed: {message}", file=sys.stderr)
        return 1
    print(
        "acceptance metrics written; "
        f"m1={result.m1_metric_thresholds_passed} "
        f"m2={result.m2_metric_thresholds_passed} "
        "external_acceptance=False scope=DECLARED_SUPPORT_METRICS_ONLY"
    )
    phase_passed = {
        "M1": result.m1_metric_thresholds_passed,
        "M2": result.m2_metric_thresholds_passed,
        "ALL": result.all_metric_thresholds_passed,
    }[args.required_phase]
    if not phase_passed:
        print(
            f"required metric phase {args.required_phase} did not meet every threshold",
            file=sys.stderr,
        )
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
