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

echo "=== Pass 2: dynamic files (HTML, assets, stats, small data) ==="
# Sync web/ root (HTML, JS, txt files)
rsync "${RSYNC_FLAGS[@]}" \
  "$ROOT/web/" "$TARGET/"

# Sync stats/ with --delete (small, fully managed)
rsync "${RSYNC_FLAGS[@]}" --delete \
  "$ROOT/data/v1/stats/" "$TARGET/data/v1/stats/"

# Sync small/dynamic data dirs (no --delete — don't remove files we're not syncing)
for dir in deputati comisii declaratii declaratii-interese motiuni stenograme doc-comisii correspondence; do
  if [[ -d "$ROOT/data/v1/$dir" ]]; then
    rsync "${RSYNC_FLAGS[@]}" "$ROOT/data/v1/$dir/" "$TARGET/data/v1/$dir/"
  fi
done

# Sync last_updated.json (updated every run)
rsync "${RSYNC_FLAGS[@]}" \
  "$ROOT/data/v1/last_updated.json" "$TARGET/data/v1/" 2>/dev/null || true

# Sync assets/
rsync "${RSYNC_FLAGS[@]}" \
  "$ROOT/assets/" "$TARGET/assets/"

echo ""
echo "Deploy complete → $TARGET"
