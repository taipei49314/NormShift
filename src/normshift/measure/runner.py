"""Run measurement suite against frozen labels (fail-closed)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from normshift import __version__
from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.measure.scoring import (
    AlignmentGoldItem,
    AlignmentPrediction,
    ExtractionGoldItem,
    ExtractionPrediction,
    macro_average,
    score_alignment,
    score_classification,
    score_extraction,
)
from normshift.model.types import AdapterName, ProfileName
from normshift.pipeline import run_diff


class MeasureError(Exception):
    """Fail-closed measurement error (invalid suite / missing inputs)."""


@dataclass
class CaseMeasureResult:
    case_id: str
    passed: bool
    extraction: dict[str, Any]
    alignment: dict[str, Any]
    classification: dict[str, Any]
    detail: str = ""


@dataclass
class MeasureReport:
    schema_version: str = "1.0.0"
    tool_version: str = __version__
    ground_truth_path: str = ""
    ground_truth_sha256: str = ""
    case_count: int = 0
    cases_passed: int = 0
    cases_failed: int = 0
    extraction: dict[str, float] = field(default_factory=dict)
    alignment: dict[str, float] = field(default_factory=dict)
    classification: dict[str, float] = field(default_factory=dict)
    case_results: list[CaseMeasureResult] = field(default_factory=list)
    integrity: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.case_count > 0 and self.cases_failed == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tool_version": self.tool_version,
            "ground_truth_path": self.ground_truth_path,
            "ground_truth_sha256": self.ground_truth_sha256,
            "case_count": self.case_count,
            "cases_passed": self.cases_passed,
            "cases_failed": self.cases_failed,
            "extraction": dict(sorted(self.extraction.items())),
            "alignment": dict(sorted(self.alignment.items())),
            "classification": dict(sorted(self.classification.items())),
            "case_results": [
                {
                    "case_id": c.case_id,
                    "passed": c.passed,
                    "extraction": c.extraction,
                    "alignment": c.alignment,
                    "classification": c.classification,
                    "detail": c.detail,
                }
                for c in sorted(self.case_results, key=lambda x: x.case_id)
            ],
            "integrity": dict(sorted(self.integrity.items())),
        }


def _resolve_path(base: Path, value: str) -> Path:
    p = Path(value)
    if p.is_file():
        return p
    cand = (base / value).resolve()
    if cand.is_file():
        return cand
    cand2 = (Path.cwd() / value).resolve()
    if cand2.is_file():
        return cand2
    raise MeasureError(f"Cannot resolve path: {value}")


def _load_cases(ground_truth: Path) -> list[dict[str, Any]]:
    if not ground_truth.is_file():
        raise MeasureError(f"Ground truth not found: {ground_truth}")
    text = ground_truth.read_text(encoding="utf-8").strip()
    if not text:
        raise MeasureError(f"Ground truth is empty: {ground_truth}")
    cases: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise MeasureError(f"Invalid JSONL at line {line_no}: {exc}") from exc
        if not isinstance(obj, dict) or "id" not in obj:
            raise MeasureError(f"Case at line {line_no} must be object with id")
        cases.append(obj)
    if not cases:
        raise MeasureError(f"No cases in ground truth: {ground_truth}")
    return cases


def _sha256_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extraction_gold_from_case(case: dict[str, Any], side: str) -> list[ExtractionGoldItem]:
    raw = case.get("expected_extractions") or {}
    items = raw.get(side) if isinstance(raw, dict) else None
    if items is None:
        # Infer zero-extraction for empty expected classifications + forbids on self-diff
        if case.get("infer_empty_extraction"):
            return []
        return []  # no gold → perfect empty score only if we treat as no-op; runner uses explicit
    out: list[ExtractionGoldItem] = []
    for it in items:
        if isinstance(it, str):
            out.append(ExtractionGoldItem(contains=it))
        elif isinstance(it, dict):
            out.append(
                ExtractionGoldItem(
                    contains=str(it.get("contains") or it.get("text") or ""),
                    modality=str(it["modality"]) if it.get("modality") else None,
                )
            )
    return [g for g in out if g.contains]


def _alignment_gold_from_case(case: dict[str, Any]) -> list[AlignmentGoldItem]:
    items = case.get("expected_alignments") or []
    out: list[AlignmentGoldItem] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        out.append(
            AlignmentGoldItem(
                old_contains=str(it.get("old_contains") or ""),
                new_contains=str(it.get("new_contains") or ""),
                aligned=bool(it.get("aligned", True)),
            )
        )
    return [g for g in out if g.old_contains and g.new_contains]


def run_measure(ground_truth: Path) -> MeasureReport:
    """Execute measurement suite. Raises MeasureError on invalid suite."""
    cases = _load_cases(ground_truth)
    base = ground_truth.parent
    report = MeasureReport(
        ground_truth_path=str(ground_truth.as_posix()),
        ground_truth_sha256=_sha256_file(ground_truth),
    )

    ext_dicts: list[dict[str, Any]] = []
    ali_dicts: list[dict[str, Any]] = []
    cls_dicts: list[dict[str, Any]] = []

    for case in cases:
        case_id = str(case["id"])
        try:
            profile = ProfileName(str(case.get("profile", "rfc2119")))
            adapter = AdapterName(str(case.get("adapter", "auto")))
            old_path = _resolve_path(base, str(case["old"]))
            new_path = _resolve_path(base, str(case["new"]))

            # One immutable load per path for the whole case
            from normshift.extract.extractor import extract_from_source
            from normshift.source import load_immutable_source

            old_src = load_immutable_source(old_path, adapter=adapter)
            new_src = load_immutable_source(new_path, adapter=adapter)
            old_doc = extract_from_source(old_src, profile)
            new_doc = extract_from_source(new_src, profile)
            diff = run_diff(
                old_path,
                new_path,
                profile=profile,
                adapter=adapter,
                old_source=old_src,
                new_source=new_src,
            )

            # Extraction: score old+new jointly as multiset of predictions vs gold
            gold_ext = _extraction_gold_from_case(case, "old") + _extraction_gold_from_case(
                case, "new"
            )
            # If no expected_extractions key at all, score self-consistency: both sides
            # must extract same count for identical files when specified
            has_ext_key = "expected_extractions" in case
            preds_ext = [
                ExtractionPrediction(text=r.normalized_text, modality=r.modality.value)
                for r in (old_doc.requirements + new_doc.requirements)
            ]
            if has_ext_key:
                em = score_extraction(preds_ext, gold_ext)
            else:
                # Neutral 1.0 when not labeled — still numeric, does not invent gold
                em = score_extraction([], [])
                em = type(em)(
                    precision=1.0,
                    recall=1.0,
                    f1=1.0,
                    true_positives=0,
                    false_positives=0,
                    false_negatives=0,
                    gold_count=0,
                    pred_count=len(preds_ext),
                )

            # Alignment gold
            gold_ali = _alignment_gold_from_case(case)
            has_ali_key = "expected_alignments" in case
            pred_ali: list[AlignmentPrediction] = []
            for ch in diff.changes:
                if ch.old_text and ch.new_text and ch.old_requirement_id and ch.new_requirement_id:
                    pred_ali.append(
                        AlignmentPrediction(
                            old_text=ch.old_text,
                            new_text=ch.new_text,
                            aligned=True,
                        )
                    )
            if has_ali_key:
                am = score_alignment(pred_ali, gold_ali)
            else:
                am = score_alignment([], [])
                am = type(am)(
                    precision=1.0,
                    recall=1.0,
                    f1=1.0,
                    true_positives=0,
                    false_positives=0,
                    false_negatives=0,
                    gold_positive_pairs=0,
                    pred_positive_pairs=len(pred_ali),
                )

            # Classification
            focus = list(case.get("focus_substrings") or [])
            changes = diff.changes
            if focus:
                changes = [
                    c
                    for c in changes
                    if any(
                        s.lower() in ((c.old_text or "") + (c.new_text or "")).lower()
                        for s in focus
                    )
                ]
            observed = [c.classification.value for c in changes]
            expected = [
                str(x)
                for x in (case.get("expected_classifications") or case.get("expected") or [])
            ]
            forbid = [str(x) for x in (case.get("forbid_classifications") or [])]
            allow_extra = bool(case.get("allow_extra", True))
            cm = score_classification(
                observed,
                expected,
                allow_extra=allow_extra,
                forbid=forbid or None,
            )

            # Case pass: classification must pass; extraction/alignment pass when labeled
            passed = cm.case_passed
            if has_ext_key:
                passed = passed and em.f1 >= float(case.get("extraction_f1_min", 1.0))
            if has_ali_key:
                passed = passed and am.f1 >= float(case.get("alignment_f1_min", 1.0))

            detail = "ok" if passed else "metric gate failed"
            result = CaseMeasureResult(
                case_id=case_id,
                passed=passed,
                extraction=em.to_dict(),
                alignment=am.to_dict(),
                classification=cm.to_dict(),
                detail=detail,
            )
        except MeasureError:
            raise
        except Exception as exc:  # noqa: BLE001
            result = CaseMeasureResult(
                case_id=case_id,
                passed=False,
                extraction={"precision": 0.0, "recall": 0.0, "f1": 0.0},
                alignment={"precision": 0.0, "recall": 0.0, "f1": 0.0},
                classification={"precision": 0.0, "recall": 0.0, "f1": 0.0, "case_passed": False},
                detail=f"error: {exc}",
            )

        report.case_results.append(result)
        report.case_count += 1
        if result.passed:
            report.cases_passed += 1
        else:
            report.cases_failed += 1
        ext_dicts.append(result.extraction)
        ali_dicts.append(result.alignment)
        cls_dicts.append(result.classification)

    keys = ("precision", "recall", "f1")
    report.extraction = macro_average(ext_dicts, keys)
    report.alignment = macro_average(ali_dicts, keys)
    report.classification = macro_average(cls_dicts, keys)
    # Add case pass rate to classification aggregate
    report.classification["case_pass_rate"] = (
        round(report.cases_passed / report.case_count, 4) if report.case_count else 0.0
    )

    data = report.to_dict()
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.integrity = data["integrity"]
    return report


def write_metrics(report: MeasureReport, path: Path) -> str:
    """Write canonical metrics JSON. Only call after successful run_measure."""
    import hashlib

    from normshift.io_safety import atomic_write_bytes

    data = report.to_dict()
    digest = integrity_payload_hash(data)
    data["integrity"] = {"alg": "sha256", "content_sha256": digest}
    raw = canonical_json_bytes(data)
    atomic_write_bytes(path, raw)
    return hashlib.sha256(raw).hexdigest()
