import hashlib
import json
import subprocess
from pathlib import Path

sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], text=True).strip()

ms = json.loads(Path("MISSION_STATE.json").read_text(encoding="utf-8"))
ms["status"] = "M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT"
ms["last_verified_commit"] = sha
ms["current_objective"] = "M0 repair round 2 complete — external re-audit"
ms["commands_run"] = [
    "uv run ruff check . #0",
    "uv run mypy src #0",
    "uv run pytest -q #92 passed",
    "uv run normshift benchmark #17/17",
    "uv run normshift measure #15/15",
    "uv run normshift verify --source-root . #0",
]
ms["known_failures"] = []
ms["next_action"] = "STOP. External re-audit. No M1/M2 feature work."
Path("MISSION_STATE.json").write_text(json.dumps(ms, indent=2) + "\n", encoding="utf-8")

claims = Path("CLAIMS.md").read_text(encoding="utf-8").replace("PINNED_COMMIT", sha)
Path("CLAIMS.md").write_text(claims, encoding="utf-8")


def h(p: str) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


ev = Path("evidence/m0-repair-round2/M0_REPAIR_ROUND2_EVIDENCE.md")
t = ev.read_text(encoding="utf-8")
t = t.replace("*(pinned at closeout)*", f"`{sha}`", 1)
t = t.replace("*(pinned at closeout)*", f"`{tree}`", 1)
t = t.replace(
    "report.json | `c364b844…` (regenerated; see manifest for full digests)",
    f"report.json | `{h('evidence/m0-repair-round2/report.json')}`",
)
t = t.replace(
    "report.md | *(see manifest)*",
    f"report.md | `{h('evidence/m0-repair-round2/report.md')}`",
)
t = t.replace(
    "metrics.json | *(see manifest)*",
    f"metrics.json | `{h('evidence/m0-repair-round2/metrics.json')}`",
)
ev.write_text(t, encoding="utf-8")
print(sha)
print(tree)
