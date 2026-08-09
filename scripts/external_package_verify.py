#!/usr/bin/env python3
"""Verify an exact-subject NormShift package and emit bounded JSON."""

from __future__ import annotations

import importlib.metadata
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_MARKER = "NORMSHIFT_PACKAGE_VERIFIER_BOOTSTRAPPED"
BOOTSTRAP_REQUIREMENTS = (
    "jsonschema==4.26.0",
    "packaging==26.3",
    "cyclonedx-python-lib[validation]==11.11.0",
)


def _bootstrap() -> int | None:
    if os.environ.get(BOOTSTRAP_MARKER) == "1":
        if sys.version_info[:2] != (3, 12):
            print("error: package verifier requires Python 3.12", file=sys.stderr)
            return 1
        for requirement in BOOTSTRAP_REQUIREMENTS:
            distribution, expected = requirement.split("==", maxsplit=1)
            distribution = distribution.split("[", maxsplit=1)[0]
            if importlib.metadata.version(distribution) != expected:
                print(f"error: bootstrap dependency mismatch: {requirement}", file=sys.stderr)
                return 1
        return None
    uv = shutil.which("uv")
    if uv is None:
        print("error: uv is required to bootstrap the exact package verifier", file=sys.stderr)
        return 1
    environment = os.environ.copy()
    environment[BOOTSTRAP_MARKER] = "1"
    command = [uv, "run", "--no-project", "--python", "3.12"]
    for requirement in BOOTSTRAP_REQUIREMENTS:
        command.extend(("--with", requirement))
    command.extend(("python", "-B", str(Path(__file__).resolve()), *sys.argv[1:]))
    return subprocess.run(command, env=environment, check=False).returncode


def _main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from normshift.audit.package_verify import main

    return main()


if __name__ == "__main__":
    bootstrap_result = _bootstrap()
    raise SystemExit(_main() if bootstrap_result is None else bootstrap_result)
