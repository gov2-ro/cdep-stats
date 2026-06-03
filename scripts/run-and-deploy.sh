#!/usr/bin/env bash
# Run data pipeline + deploy in one go.
#
# Usage:
#   ./scripts/run-and-deploy.sh daily [deploy-target]     # scrape + build + quick deploy
#   ./scripts/run-and-deploy.sh weekly [deploy-target]    # slower scrape + full deploy
#
# Examples:
#   ./scripts/run-and-deploy.sh daily                     # just scrape/build, no deploy
#   ./scripts/run-and-deploy.sh daily pax@example.com:~/public_html
#   ./scripts/run-and-deploy.sh weekly pax@example.com:~/public_html

set -euo pipefail

CADENCE="${1:-}"
TARGET="${2:-}"

if [[ -z "$CADENCE" ]] || [[ "$CADENCE" != "daily" && "$CADENCE" != "weekly" ]]; then
  echo "Usage: $0 {daily|weekly} [deploy-target]" >&2
  echo "" >&2
  echo "Examples:" >&2
  echo "  $0 daily                              # scrape + build only" >&2
  echo "  $0 daily pax@host:/path/to/public_html  # scrape + build + deploy --quick" >&2
  echo "  $0 weekly pax@host:/path/to/public_html # scrape + build + deploy (full)" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEPLOY_QUICK=0
DEPLOY_MODE="—"

if [[ -n "$TARGET" ]]; then
  if [[ "$CADENCE" == "daily" ]]; then
    DEPLOY_QUICK=1
    DEPLOY_MODE="--quick"
  else
    DEPLOY_MODE="(full)"
  fi
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Data Pipeline + Deploy — $CADENCE mode                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Phase 1: Scrape + Build (cadence: $CADENCE)"
echo "Phase 2: Deploy to $TARGET $DEPLOY_MODE"
echo ""

# Phase 1: Run refresh_all.py
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$ROOT/scripts/refresh_all.py" --cadence "$CADENCE"
REFRESH_EXIT=$?

if [[ $REFRESH_EXIT -ne 0 ]]; then
  echo ""
  echo "❌ Data pipeline failed (exit $REFRESH_EXIT). Skipping deploy."
  exit $REFRESH_EXIT
fi

echo ""
echo "✓ Data pipeline completed successfully."
echo ""

# Phase 2: Deploy (if target specified)
if [[ -n "$TARGET" ]]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  if [[ $DEPLOY_QUICK -eq 1 ]]; then
    echo "Deploying (--quick mode)..."
    bash "$ROOT/scripts/deploy.sh" --quick "$TARGET"
  else
    echo "Deploying (full mode)..."
    bash "$ROOT/scripts/deploy.sh" "$TARGET"
  fi
  DEPLOY_EXIT=$?

  if [[ $DEPLOY_EXIT -ne 0 ]]; then
    echo ""
    echo "❌ Deploy failed (exit $DEPLOY_EXIT)."
    exit $DEPLOY_EXIT
  fi

  echo ""
  echo "✓ Deploy completed successfully."
else
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "No deploy target specified. To deploy next time, run:"
  echo "  ./scripts/run-and-deploy.sh $CADENCE pax@host:/path/to/public_html"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✓ All done!                                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
