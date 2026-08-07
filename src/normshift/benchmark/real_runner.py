"""Provisional real-standards benchmark (AUTO labels only — not gold)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from normshift.extract.extractor import extract_from_source
from normshift.model.types import AdapterName, ProfileName
from normshift.pipeline import run_diff
from normshift.source import load_immutable_source


@dataclass
class RealBenchCase:
    case_id: str
    kind: str
    detail: str
    passed: bool
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class RealBenchReport:
    cases: list[RealBenchCase]
    status: str = "EXPERIMENTAL_NOT_ADJUDICATED"
    label_authority: str = "AUTO"

    @property
    def passed(self) -> int:
        return sum(1 for c in self.cases if c.passed)

    @property
    def total(self) -> int:
        return len(self.cases)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "status": self.status,
            "label_authority": self.label_authority,
            "note": "Provisional metrics over AUTO labels — not adjudicated gold.",
            "passed": self.passed,
            "total": self.total,
            "cases": [
                {
                    "case_id": c.case_id,
                    "kind": c.kind,
                    "detail": c.detail,
                    "passed": c.passed,
                    "metrics": c.metrics,
                }
                for c in self.cases
            ],
        }


def run_real_benchmark(root: Path) -> RealBenchReport:
    """Smoke + consistency checks on in-repo corpus fixtures (offline)."""
    root = Path(root)
    cases: list[RealBenchCase] = []
    fixtures = [
        (
            "rfc",
            root / "fixtures/corpus/rfc/sample-v1.html",
            AdapterName.RFC,
            ProfileName.RFC2119,
        ),
        (
            "w3c",
            root / "fixtures/corpus/w3c/sample-v1.html",
            AdapterName.W3C,
            ProfileName.RFC2119,
        ),
        (
            "whatwg",
            root / "fixtures/corpus/whatwg/sample-v1.html",
            AdapterName.WHATWG,
            ProfileName.WHATWG,
        ),
    ]
    for fam, path, adapter, profile in fixtures:
        if not path.is_file():
            cases.append(
                RealBenchCase(fam + "-extract", "extraction", "missing fixture", False)
            )
            continue
        src = load_immutable_source(path, adapter=adapter)
        doc = extract_from_source(src, profile)
        n = len(doc.requirements)
        locators = [r.source_locator for r in doc.requirements]
        stable = len(locators) == len(set(locators))
        cases.append(
            RealBenchCase(
                case_id=f"{fam}-extract",
                kind="extraction",
                detail=f"{n} requirements",
                passed=n >= 1 and stable,
                metrics={
                    "requirement_count": n,
                    "unique_locators": len(set(locators)),
                    "locator_stability": stable,
                },
            )
        )

    pairs = [
        (
            "rfc-pair",
            root / "fixtures/corpus/rfc/sample-v1.html",
            root / "fixtures/corpus/rfc/sample-v2.html",
            AdapterName.RFC,
            ProfileName.RFC2119,
        ),
        (
            "w3c-pair",
            root / "fixtures/corpus/w3c/sample-v1.html",
            root / "fixtures/corpus/w3c/sample-v2.html",
            AdapterName.W3C,
            ProfileName.RFC2119,
        ),
        (
            "whatwg-pair",
            root / "fixtures/corpus/whatwg/sample-v1.html",
            root / "fixtures/corpus/whatwg/sample-v2.html",
            AdapterName.WHATWG,
            ProfileName.WHATWG,
        ),
    ]
    for pid, old, new, adapter, profile in pairs:
        if not old.is_file() or not new.is_file():
            cases.append(RealBenchCase(pid, "alignment", "missing", False))
            continue
        report = run_diff(old, new, profile=profile, adapter=adapter, source_root=root)
        amb = sum(1 for c in report.changes if c.classification.value == "AMBIGUOUS")
        cases.append(
            RealBenchCase(
                case_id=pid,
                kind="alignment_classification",
                detail=f"{len(report.changes)} changes, {amb} ambiguous",
                passed=len(report.changes) >= 1,
                metrics={
                    "old_requirements": len(report.old_requirements),
                    "new_requirements": len(report.new_requirements),
                    "changes": len(report.changes),
                    "ambiguous": amb,
                    "ambiguity_rate": (
                        amb / len(report.changes) if report.changes else 0.0
                    ),
                },
            )
        )

    # Offline replay: generate twice, compare classification multiset
    old = root / "fixtures/corpus/rfc/sample-v1.html"
    new = root / "fixtures/corpus/rfc/sample-v2.html"
    if old.is_file() and new.is_file():
        r1 = run_diff(
            old, new, profile=ProfileName.RFC2119, adapter=AdapterName.RFC, source_root=root
        )
        r2 = run_diff(
            old, new, profile=ProfileName.RFC2119, adapter=AdapterName.RFC, source_root=root
        )
        c1 = sorted(c.classification.value for c in r1.changes)
        c2 = sorted(c.classification.value for c in r2.changes)
        cases.append(
            RealBenchCase(
                case_id="offline-replay-determinism",
                kind="offline_replay",
                detail="classification multiset identity",
                passed=c1 == c2,
                metrics={"classifications": c1},
            )
        )

    return RealBenchReport(cases=cases)
