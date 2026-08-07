# Capsule Format

See `capsules/<pair_id>/capsule.json`.

- **Full** (`offline_replay=true`): includes `source/*.document` bytes when redistribution permits.
- **Thin** (`offline_replay=false`, `blocking_reason=SOURCE_BYTES_NOT_INCLUDED`): manifests + reports only.

Verify: `normshift capsule verify capsules/PAIR_ID`
