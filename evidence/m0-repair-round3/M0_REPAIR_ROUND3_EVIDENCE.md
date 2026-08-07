# M0 Repair Round 3 Evidence

**Implementer status (max):** `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`  
**Package identity:** external MANIFEST / bundle HEAD (not self-referential SHA)

## Defects closed vs EXTERNAL_AUDIT_R2

| ID | Fix |
|----|-----|
| P0-01 portable evidence | `source_ref` portable POSIX paths; `--source-root` resolves without absolute workstation binding |
| P0-01 Source.zip LF/CRLF | package via `git archive` only (blob bytes) |
| P0-02 incomplete compare | full `build_report` replay + exact model dump compare; typed summary/integrity `extra=forbid` |
| P0-03 path types/ancestry | reject symlink/dir/non-regular; reject input/output ancestors |
| P1-02 unquoted history | historical framing protects unquoted historical clauses |
| P1-03/04 fsync/cleanup | directory fsync; CleanupIncompleteError with backup paths |
| P2-01 README paths | updated to round3 evidence |

## Gates

```text
uv run ruff check .     # 0
uv run mypy src         # 0
uv run pytest -q        # 108+
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
uv run normshift measure ... evidence/m0-repair-round3/metrics.json
uv run normshift diff ... evidence/m0-repair-round3/report.json
uv run normshift verify evidence/m0-repair-round3/report.json --source-root .  # 0
# relocation: copy tree to new abs path, verify with --source-root B → 0
```

## Portable source refs (example)

```text
old_document.path = fixtures/synthetic/spec-v1.html
provenance.local_path = fixtures/synthetic/spec-v1.html
```

## Known limitations

- SHA-256 is unkeyed consistency digest, not a signature.
- Multi-file commit is rollback-safe, not single-syscall global atomic.
- Package tip identity is **externally attested** in MANIFEST (not self-referential in-tree).
- M1/M2 not adjudicated.

## Next

External re-audit of R3 package products only.
