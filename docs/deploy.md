Two-pass rsync deploy with an optional quick-mode for daily deploys:

Full deploy (default)

./scripts/deploy.sh user@host:/path/to/public_html

Pass 1 — stable/immutable large data blobs (~270 MB):
- voturi/ (180 MB, ~4500 per-vote JSON files)
- declaratii-avere/ (9.7 MB)
- proiecte/ (59 MB, excluding necunoscut.json and _index.json)
- ordine-zi/ (90 MB) ← new
- interpelari/ (83 MB) ← new

Uses --checksum flag: rsync compares actual file content, not just mtime/size. After the first full
sync, only genuinely changed files transfer. This avoids re-uploading 300+ MB every time if timestamps
get touched.

Pass 2 — dynamic files (~50 MB):
- web/ → HTML, JS, txt files (all pages)
- data/v1/ → Everything except the Pass 1 dirs (includes last_updated.json, stats/, small data dirs)
- assets/ → Images, geodata, CSS

Uses --delete to clean up stale files. Excludes Pass 1 dirs to avoid redundant transfer.

Quick deploy (daily use)

./scripts/deploy.sh --quick user@host:/path/to/public_html

Skips Pass 1 entirely. Assumes those large stable blobs were already synced from a prior full deploy.
Only runs Pass 2 (~50 MB, seconds not minutes).

Typical daily workflow:
1. Run python3 scripts/refresh_all.py --cadence daily → scrapes, builds, writes last_updated.json
2. Run ./scripts/deploy.sh --quick user@host:/path → syncs new stats, footer timestamp, any daily data
changes
3. Done in ~30 seconds

Dry-run

DRY=1 ./scripts/deploy.sh user@host:/path
DRY=1 ./scripts/deploy.sh --quick user@host:/path

Adds --dry-run flag, shows what would transfer without actually uploading.

---
Why this beats the old zip flow:
- Incremental: After first full sync, subsequent deploys only transfer what changed
- Parallel-friendly: Multiple rsync operations could run in parallel if needed
- Large data stays put: Once voturi/ is uploaded, never retransfer unless content genuinely changes
- Daily sync is fast: --quick re-uploads only ~50 MB of fresh stats/HTML/last-updated, perfect for
daily cadence