#!/usr/bin/env bash
# Two-pass rsync deploy — replaces the build_web.py + scp+unzip flow.
#
# Pass 1 (stable/immutable): voturi/, declaratii-avere/, proiecte/ year files
#   Uses --checksum so only genuinely changed files transfer after first sync.
#   These dirs change rarely; checksum avoids re-sending 300+ MB every deploy.
#
# Pass 2 (dynamic): everything else — HTML, assets, stats, small data dirs.
#   Uses --delete to remove stale files. Fast because these dirs are small.
#
# Usage:
#   ./scripts/deploy.sh user@host:/path/to/public_html
#
# Requirements: rsync on both ends, SSH key auth configured.
#
# Dry-run:
#   DRY=1 ./scripts/deploy.sh user@host:/path/to/public_html

set -euo pipefail

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 user@host:/path/to/public_html" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY="${DRY:-}"
RSYNC_FLAGS=(-az --progress)
[[ -n "$DRY" ]] && RSYNC_FLAGS+=(--dry-run) && echo "[DRY RUN]"

echo "=== Pass 1: stable data (checksum, no delete) ==="
rsync "${RSYNC_FLAGS[@]}" --checksum \
  "$ROOT/data/v1/voturi/" "$TARGET/data/v1/voturi/"

rsync "${RSYNC_FLAGS[@]}" --checksum \
  "$ROOT/data/v1/declaratii-avere/" "$TARGET/data/v1/declaratii-avere/"

# proiecte year files only (necunoscut.json excluded — too large)
rsync "${RSYNC_FLAGS[@]}" --checksum \
  --exclude='necunoscut.json' --exclude='_index.json' \
  "$ROOT/data/v1/proiecte/" "$TARGET/data/v1/proiecte/"

echo ""
echo "=== Pass 2: dynamic files (HTML, assets, stats, small data) ==="
rsync "${RSYNC_FLAGS[@]}" --delete \
  --exclude='data/v1/voturi/' \
  --exclude='data/v1/declaratii-avere/' \
  --exclude='data/v1/proiecte/' \
  --exclude='data/v1/amendamente/' \
  "$ROOT/web/" "$TARGET/"

rsync "${RSYNC_FLAGS[@]}" --delete \
  --exclude='voturi/' \
  --exclude='declaratii-avere/' \
  --exclude='proiecte/' \
  --exclude='amendamente/' \
  "$ROOT/data/v1/" "$TARGET/data/v1/"

rsync "${RSYNC_FLAGS[@]}" --delete \
  "$ROOT/assets/" "$TARGET/assets/"

echo ""
echo "Deploy complete → $TARGET"
