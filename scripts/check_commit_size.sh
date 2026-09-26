#!/usr/bin/env bash
# ==============================================================================
# PR Total Diff Size Checker (Max 200 lines per PR)
#
# Enforces the rule: The total PR diff must not exceed 200 lines of code change
# (added + deleted lines), excluding lockfiles, binary files, and generated assets.
# Suitable for squash-merge workflows where the whole PR lands as a single commit.
# ==============================================================================

set -euo pipefail

MAX_LINES=200

# Determine base reference
BASE_REF="${1:-${GITHUB_BASE_REF:-}}"

if [ -z "$BASE_REF" ]; then
  # If no base provided, check if origin/main exists
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    BASE_REF="origin/main"
  elif git rev-parse --verify main >/dev/null 2>&1; then
    BASE_REF="main"
  else
    BASE_REF="HEAD~1"
  fi
fi

# Determine diff target range
if [[ "$BASE_REF" == *".."* ]]; then
  DIFF_TARGET="$BASE_REF"
else
  # If BASE_REF is at the same commit as HEAD and working tree has changes, compare against BASE_REF directly
  if git rev-parse --verify "$BASE_REF" >/dev/null 2>&1 && [ "$(git rev-parse HEAD)" = "$(git rev-parse "$BASE_REF")" ]; then
    DIFF_TARGET="$BASE_REF"
  else
    DIFF_TARGET="${BASE_REF}...HEAD"
  fi
fi

echo "================================================================="
echo "  PR Total Diff Size Check (Max allowed: ${MAX_LINES} lines / PR)"
echo "  Target Range: $DIFF_TARGET"
echo "================================================================="

# File ignore patterns (pathspec exclude syntax)
EXCLUDES=(
  ':!package-lock.json'
  ':!yarn.lock'
  ':!pnpm-lock.yaml'
  ':!Pipfile.lock'
  ':!poetry.lock'
  ':!*.min.js'
  ':!*.min.css'
  ':!*.svg'
  ':!*.png'
  ':!*.jpg'
  ':!*.jpeg'
  ':!*.ico'
  ':!*.webp'
)

# Calculate total lines changed (added + deleted)
ADDED_TOTAL=0
DELETED_TOTAL=0

NUMSTAT=$(git diff --numstat "$DIFF_TARGET" -- . "${EXCLUDES[@]}" 2>/dev/null || true)

while IFS=$'\t' read -r added deleted file; do
  # Skip empty lines or binary files where added/deleted is '-'
  if [ -n "$added" ] && [ "$added" != "-" ]; then
    ADDED_TOTAL=$((ADDED_TOTAL + added))
  fi
  if [ -n "$deleted" ] && [ "$deleted" != "-" ]; then
    DELETED_TOTAL=$((DELETED_TOTAL + deleted))
  fi
done <<< "$NUMSTAT"

TOTAL_CHANGED=$((ADDED_TOTAL + DELETED_TOTAL))

# Also capture git diff --shortstat
SHORTSTAT=$(git diff --shortstat "$DIFF_TARGET" -- . "${EXCLUDES[@]}" 2>/dev/null || true)
SHORTSTAT=$(echo "$SHORTSTAT" | sed 's/^[[:space:]]*//')

if [ -z "$SHORTSTAT" ]; then
  SHORTSTAT="0 files changed, 0 insertions(+), 0 deletions(-)"
fi

echo ""
echo "📊 Total PR Diff Stats:"
echo "   Summary:  $SHORTSTAT"
echo "   Measured: +$ADDED_TOTAL / -$DELETED_TOTAL (${TOTAL_CHANGED} lines total)"
echo ""

if [ "$TOTAL_CHANGED" -gt "$MAX_LINES" ]; then
  echo "❌ VIOLATION: This PR's total diff exceeds ${MAX_LINES} lines limit!"
  echo "   Diff range: $DIFF_TARGET"
  echo "   Total:      $TOTAL_CHANGED lines (+$ADDED_TOTAL / -$DELETED_TOTAL)"
  echo ""
  echo "   Files changed breakdown:"
  git diff --stat "$DIFF_TARGET" -- . "${EXCLUDES[@]}" 2>/dev/null | sed 's/^/     /'
  echo ""
  echo "================================================================="
  echo "  Result: FAILED (Total PR diff exceeds ${MAX_LINES} lines)"
  echo "================================================================="
  echo ""
  echo "How to fix:"
  echo "  1. Break large changes into smaller, logical Pull Requests:"
  echo "     Keep each PR under ${MAX_LINES} lines so it can be thoroughly reviewed."
  echo "  2. If using git rebase to split commits before squashing:"
  echo "     git rebase -i $BASE_REF"
  echo "  3. Mark the oversized commit with 'edit' (or 'e'), unstage files with:"
  echo "     git reset HEAD~1"
  echo "  4. Stage and commit changes in smaller batches (max 200 lines per PR):"
  echo "     git add -p   (or add individual files/folders)"
  echo "     git commit -m \"feat: small reviewable part 1\""
  echo "     git add ..."
  echo "     git commit -m \"feat: small reviewable part 2\""
  echo "     git rebase --continue"
  echo "  5. Push the split changes to separate branches and open smaller PRs."
  echo ""
  exit 1
else
  echo "================================================================="
  echo "  Result: PASSED (Total PR diff is within ${MAX_LINES} lines)"
  echo "================================================================="
  echo "✅ This PR's total diff is within the ${MAX_LINES}-line limit! 🎉"
  exit 0
fi
