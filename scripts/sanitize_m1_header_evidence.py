"""Deterministically reduce M1 curator HTTP headers to a safe allowlist."""

from normshift.corpus.header_sanitization import main

if __name__ == "__main__":
    raise SystemExit(main())
