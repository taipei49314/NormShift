"""Pure scorers: predicted vs gold → numeric metrics (no I/O)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _round4(x: float) -> float:
    return round(float(x), 4)


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else (1.0 if fn == 0 else 0.0)
    recall = tp / (tp + fn) if (tp + fn) else (1.0 if fp == 0 else 0.0)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return _round4(precision), _round4(recall), _round4(f1)


@dataclass(frozen=True)
class ExtractionGoldItem:
    """A gold requirement descriptor (substring + optional modality)."""

    contains: str
    modality: str | None = None


@dataclass(frozen=True)
class ExtractionPrediction:
    text: str
    modality: str


@dataclass
class ExtractionMetrics:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int
    gold_count: int
    pred_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AlignmentGoldItem:
    old_contains: str
    new_contains: str
    aligned: bool = True


@dataclass(frozen=True)
class AlignmentPrediction:
    old_text: str
    new_text: str
    aligned: bool


@dataclass
class AlignmentMetrics:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int
    gold_positive_pairs: int
    pred_positive_pairs: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ClassificationMetrics:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int
    expected: list[str] = field(default_factory=list)
    observed: list[str] = field(default_factory=list)
    case_passed: bool = False
    exact_pass: bool = False
    permissive_pass: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_extraction(
    predicted: list[ExtractionPrediction],
    gold: list[ExtractionGoldItem],
) -> ExtractionMetrics:
    """Match gold items to predictions by substring (+ optional modality)."""
    used: set[int] = set()
    tp = 0
    for g in gold:
        needle = g.contains.lower()
        found = False
        for i, pred in enumerate(predicted):
            if i in used:
                continue
            if needle not in pred.text.lower():
                continue
            if g.modality is not None and pred.modality != g.modality:
                continue
            used.add(i)
            tp += 1
            found = True
            break
        _ = found
    fp = len(predicted) - len(used)
    fn = len(gold) - tp
    # When gold is empty: perfect if no predictions; else all preds are FP.
    if not gold:
        tp, fp, fn = 0, len(predicted), 0
        if not predicted:
            prec, rec, f1 = 1.0, 1.0, 1.0
        else:
            prec, rec, f1 = 0.0, 1.0, 0.0
        return ExtractionMetrics(
            precision=prec,
            recall=rec,
            f1=f1,
            true_positives=0,
            false_positives=fp,
            false_negatives=0,
            gold_count=0,
            pred_count=len(predicted),
        )
    prec, rec, f1 = _prf(tp, fp, fn)
    return ExtractionMetrics(
        precision=prec,
        recall=rec,
        f1=f1,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        gold_count=len(gold),
        pred_count=len(predicted),
    )


def score_alignment(
    predicted: list[AlignmentPrediction],
    gold: list[AlignmentGoldItem],
) -> AlignmentMetrics:
    """Score positive alignment pairs only (aligned=True gold items)."""
    gold_pos = [g for g in gold if g.aligned]
    pred_pos = [p for p in predicted if p.aligned]

    used: set[int] = set()
    tp = 0
    for g in gold_pos:
        for i, p in enumerate(pred_pos):
            if i in used:
                continue
            if g.old_contains.lower() not in p.old_text.lower():
                continue
            if g.new_contains.lower() not in p.new_text.lower():
                continue
            used.add(i)
            tp += 1
            break
    fp = len(pred_pos) - len(used)
    fn = len(gold_pos) - tp

    if not gold_pos:
        if not pred_pos:
            prec, rec, f1 = 1.0, 1.0, 1.0
        else:
            # No gold positives: any predicted positive is FP noise for this case.
            prec, rec, f1 = 0.0, 1.0, 0.0
            fp = len(pred_pos)
            tp = 0
            fn = 0
        return AlignmentMetrics(
            precision=prec,
            recall=rec,
            f1=f1,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            gold_positive_pairs=0,
            pred_positive_pairs=len(pred_pos),
        )

    prec, rec, f1 = _prf(tp, max(fp, 0), fn)
    return AlignmentMetrics(
        precision=prec,
        recall=rec,
        f1=f1,
        true_positives=tp,
        false_positives=max(fp, 0),
        false_negatives=fn,
        gold_positive_pairs=len(gold_pos),
        pred_positive_pairs=len(pred_pos),
    )


def score_classification(
    observed: list[str],
    expected: list[str],
    *,
    allow_extra: bool = True,
    forbid: list[str] | None = None,
) -> ClassificationMetrics:
    """Multiset label scoring with optional forbid list."""
    from collections import Counter

    exp_c = Counter(expected)
    obs_c = Counter(observed)
    forbid_set = set(forbid or [])

    if forbid_set and any(c in forbid_set for c in obs_c):
        bad = sum(obs_c[c] for c in forbid_set if c in obs_c)
        return ClassificationMetrics(
            precision=0.0,
            recall=0.0,
            f1=0.0,
            true_positives=0,
            false_positives=bad,
            false_negatives=sum(exp_c.values()),
            expected=sorted(expected),
            observed=sorted(observed),
            case_passed=False,
            exact_pass=False,
            permissive_pass=False,
        )

    if not expected and not forbid_set:
        if len(observed) == 0:
            return ClassificationMetrics(
                precision=1.0,
                recall=1.0,
                f1=1.0,
                true_positives=0,
                false_positives=0,
                false_negatives=0,
                expected=[],
                observed=sorted(observed),
                case_passed=True,
                exact_pass=True,
                permissive_pass=True,
            )
        # empty expected + observations: FP = all observations
        fp = len(observed)
        prec, rec, f1 = _prf(0, fp, 0)
        return ClassificationMetrics(
            precision=prec,
            recall=1.0,
            f1=f1,
            true_positives=0,
            false_positives=fp,
            false_negatives=0,
            expected=[],
            observed=sorted(observed),
            case_passed=bool(allow_extra),
            exact_pass=False,
            permissive_pass=bool(allow_extra),
        )

    if not expected and forbid_set:
        forbidden_hits = [c for c in observed if c in forbid_set]
        ok = len(forbidden_hits) == 0
        # All observations are FP when expected empty
        fp = len(observed)
        prec, rec, f1 = _prf(0, fp, 0) if observed else (1.0, 1.0, 1.0)
        return ClassificationMetrics(
            precision=prec if observed else 1.0,
            recall=1.0,
            f1=f1 if observed else 1.0,
            true_positives=0,
            false_positives=fp,
            false_negatives=0,
            expected=[],
            observed=sorted(observed),
            case_passed=ok,
            exact_pass=ok and len(observed) == 0,
            permissive_pass=ok,
        )

    # Multiset intersection for TP; every unmatched observed item is FP
    # (including labels not present in expected). allow_extra affects only case_passed.
    tp = sum(min(exp_c[k], obs_c.get(k, 0)) for k in exp_c)
    fn = sum(max(0, exp_c[k] - obs_c.get(k, 0)) for k in exp_c)
    fp = sum(max(0, obs_c[k] - exp_c.get(k, 0)) for k in obs_c)

    prec, rec, f1 = _prf(tp, fp, fn)
    exact_pass = exp_c == obs_c
    permissive_pass = all(obs_c.get(k, 0) >= v for k, v in exp_c.items())
    if forbid_set and any(c in forbid_set for c in obs_c):
        exact_pass = False
        permissive_pass = False
    case_passed = permissive_pass if allow_extra else exact_pass
    return ClassificationMetrics(
        precision=prec,
        recall=rec,
        f1=f1,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        expected=sorted(expected),
        observed=sorted(observed),
        case_passed=case_passed,
        exact_pass=exact_pass,
        permissive_pass=permissive_pass,
    )


def macro_average(metrics_list: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[str, float]:
    if not metrics_list:
        return {k: 0.0 for k in keys}
    out: dict[str, float] = {}
    for k in keys:
        vals = [float(m[k]) for m in metrics_list if k in m]
        out[k] = _round4(sum(vals) / len(vals)) if vals else 0.0
    return out
