"""Execute adversarial ground-truth benchmark cases."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from normshift.model.types import ProfileName
from normshift.pipeline import run_diff


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    expected: list[str]
    observed: list[str]
    detail: str = ""


@dataclass
class BenchmarkReport:
    total: int = 0
    passed: int = 0
    failed: int = 0
    results: list[CaseResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.failed == 0 and self.total > 0


def _resolve_path(base: Path, value: str) -> Path:
    p = Path(value)
    if p.is_file():
        return p
    cand = base / value
    if cand.is_file():
        return cand
    # Repo-relative from cwd
    cand2 = Path.cwd() / value
    if cand2.is_file():
        return cand2
    raise FileNotFoundError(f"Cannot resolve path: {value}")


def run_benchmark(ground_truth: Path) -> BenchmarkReport:
    if not ground_truth.is_file():
        raise FileNotFoundError(f"Ground truth not found: {ground_truth}")

    base = ground_truth.parent
    report = BenchmarkReport()

    for line_no, line in enumerate(ground_truth.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        case: dict[str, Any] = json.loads(line)
        case_id = str(case.get("id") or f"line-{line_no}")
        profile_name = str(case.get("profile", "rfc2119"))
        profile = ProfileName(profile_name)
        old_path = _resolve_path(base, str(case["old"]))
        new_path = _resolve_path(base, str(case["new"]))
        expected_raw = case.get("expected_classifications") or case.get("expected") or []
        expected = sorted(str(x) for x in expected_raw)

        # Optional filters: only classifications for specific text substrings.
        focus_substrings: list[str] = list(case.get("focus_substrings") or [])
        require_all_expected = bool(case.get("require_all_expected", True))
        allow_extra = bool(case.get("allow_extra", True))

        try:
            diff_report = run_diff(old_path, new_path, profile=profile)
        except Exception as exc:  # noqa: BLE001
            report.total += 1
            report.failed += 1
            report.results.append(
                CaseResult(
                    case_id=case_id,
                    passed=False,
                    expected=expected,
                    observed=[],
                    detail=f"Pipeline error: {exc}",
                )
            )
            continue

        changes = diff_report.changes
        if focus_substrings:
            filtered = []
            for ch in changes:
                blob = " ".join(
                    x
                    for x in (ch.old_text or "", ch.new_text or "", ch.modality_transition or "")
                    if x
                )
                if any(s.lower() in blob.lower() for s in focus_substrings):
                    filtered.append(ch)
            changes = filtered

        observed = sorted(ch.classification.value for ch in changes)

        # Matching logic:
        # - expected multiset must be subset of observed if allow_extra
        # - or exact multiset equality if not allow_extra
        from collections import Counter

        exp_c = Counter(expected)
        obs_c = Counter(observed)
        if allow_extra:
            passed = all(obs_c[k] >= v for k, v in exp_c.items()) if require_all_expected else any(
                obs_c[k] >= 1 for k in exp_c
            )
        else:
            passed = exp_c == obs_c

        # Special case: expected empty means "no substantive classifications of listed types"
        if case.get("forbid_classifications"):
            forbid = set(str(x) for x in case["forbid_classifications"])
            bad = [c for c in observed if c in forbid]
            if bad:
                passed = False
                detail = f"Forbidden classifications present: {bad}"
            else:
                detail = "No forbidden classifications."
                # still apply expected if present
                if expected and not all(obs_c[k] >= v for k, v in exp_c.items()):
                    passed = False
                    detail = f"Missing expected {expected}; observed {observed}"
        else:
            detail = "expected⊆observed" if passed else f"expected={expected} observed={observed}"

        # Determinism case handled separately by tests; optional flag.
        if case.get("check_determinism"):
            r2 = run_diff(old_path, new_path, profile=profile)
            import tempfile

            from normshift.report.builder import write_json_report

            with tempfile.TemporaryDirectory() as td:
                p1 = Path(td) / "a.json"
                p2 = Path(td) / "b.json"
                write_json_report(diff_report, p1)
                write_json_report(r2, p2)
                if p1.read_bytes() != p2.read_bytes():
                    passed = False
                    detail = "Non-deterministic JSON output across two runs."
                else:
                    detail = (detail + "; determinism ok").strip("; ")

        if case.get("check_verify_tamper"):
            import tempfile

            from normshift.report.builder import write_json_report
            from normshift.verify.verifier import verify_report_file

            with tempfile.TemporaryDirectory() as td:
                p = Path(td) / "report.json"
                write_json_report(diff_report, p)
                v1 = verify_report_file(p)
                if not v1.ok:
                    passed = False
                    detail = f"Clean report failed verify: {v1.errors}"
                else:
                    tampered = json.loads(p.read_text(encoding="utf-8"))
                    # Mutate a visible field without updating integrity.
                    if tampered.get("changes"):
                        tampered["changes"][0]["confidence"] = 0.123456
                    else:
                        tampered["summary"]["change_count"] = 999
                    tp = Path(td) / "tampered.json"
                    tp.write_text(json.dumps(tampered, indent=2), encoding="utf-8")
                    v2 = verify_report_file(tp)
                    if v2.ok:
                        passed = False
                        detail = "Tampered report incorrectly passed verify."
                    else:
                        detail = "Tamper detection ok."

        report.total += 1
        if passed:
            report.passed += 1
        else:
            report.failed += 1
        report.results.append(
            CaseResult(
                case_id=case_id,
                passed=passed,
                expected=expected,
                observed=observed,
                detail=detail,
            )
        )

    return report
