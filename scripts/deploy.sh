#!/usr/bin/env bash
# Two-pass rsync deploy — incremental data sync with optional quick-mode.
#
# Pass 1 (stable/immutable, --checksum): voturi/, declaratii-avere/, proiecte/,
#         ordine-zi/, interpelari/ — large append-only data blobs
#   Only retransfers files that genuinely changed (content checksum comparison).
#   Skip in --quick mode (assumes prior full sync already uploaded these).
#
# Pass 2 (dynamic, --delete): HTML, assets, stats, small data dirs, last_updated.json
#   Syncs frequently-changing files. Uses --delete to clean stale entries.
#
# Usage:
#   ./scripts/deploy.sh user@host:/path/to/public_html                # full deploy
#   ./scripts/deploy.sh --quick user@host:/path/to/public_html         # skip stable pass (daily use)
#
# Requirements: rsync on both ends, SSH key auth configured.
#
# Dry-run:
#   DRY=1 ./scripts/deploy.sh user@host:/path/to/public_html

set -euo pipefail

QUICK=0
TARGET=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --quick)
      QUICK=1
      shift
      ;;
    *)
      TARGET="$1"
      shift
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 [--quick] user@host:/path/to/public_html" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY="${DRY:-}"
RSYNC_FLAGS=(-az --progress)
[[ -n "$DRY" ]] && RSYNC_FLAGS+=(--dry-run) && echo "[DRY RUN]"

if [[ $QUICK -eq 0 ]]; then
  echo "=== Pass 1: stable data (checksum, no delete) ==="
  rsync "${RSYNC_FLAGS[@]}" --checksum \
    "$ROOT/data/v1/voturi/" "$TARGET/data/v1/voturi/"

  rsync "${RSYNC_FLAGS[@]}" --checksum \
    "$ROOT/data/v1/declaratii-avere/" "$TARGET/data/v1/declaratii-avere/"

  # Large append-only dirs: use checksum to avoid retransfer
  rsync "${RSYNC_FLAGS[@]}" --checksum \
    "$ROOT/data/v1/ordine-zi/" "$TARGET/data/v1/ordine-zi/"

  rsync "${RSYNC_FLAGS[@]}" --checksum \
    "$ROOT/data/v1/interpelari/" "$TARGET/data/v1/interpelari/"

  # proiecte year files only (necunoscut.json excluded — too large)
  rsync "${RSYNC_FLAGS[@]}" --checksum \
    --exclude='necunoscut.json' --exclude='_index.json' \
    "$ROOT/data/v1/proiecte/" "$TARGET/data/v1/proiecte/"

  echo ""
else
  echo "[QUICK MODE] Skipping stable/checksum pass (assumes prior full deploy)"
  echo ""
fi

echo "=== Pass 2: dynamic files (HTML, assets, stats, small data, last_updated) ==="
rsync "${RSYNC_FLAGS[@]}" --delete \
  --exclude='data/v1/voturi/' \
  --exclude='data/v1/declaratii-avere/' \
  --exclude='data/v1/proiecte/' \
  --exclude='data/v1/ordine-zi/' \
  --exclude='data/v1/interpelari/' \
  --exclude='data/v1/amendamente/' \
  "$ROOT/web/" "$TARGET/"

rsync "${RSYNC_FLAGS[@]}" --delete \
  --exclude='voturi/' \
  --exclude='declaratii-avere/' \
  --exclude='proiecte/' \
  --exclude='ordine-zi/' \
  --exclude='interpelari/' \
  --exclude='amendamente/' \
  "$ROOT/data/v1/" "$TARGET/data/v1/"

rsync "${RSYNC_FLAGS[@]}" --delete \
  "$ROOT/assets/" "$TARGET/assets/"

echo ""
echo "Deploy complete → $TARGET"
