#!/usr/bin/env bash
# ==============================================================================
# Setup Git Hooks for Aparty
# Installs a pre-push hook to check commit sizes before pushing to remote.
# ==============================================================================

set -euo pipefail

HOOK_PATH=".git/hooks/pre-push"

mkdir -p .git/hooks

cat << 'EOF' > "$HOOK_PATH"
#!/usr/bin/env bash
echo "🔍 Running pre-push commit size check..."
./scripts/check_commit_size.sh
EOF

chmod +x "$HOOK_PATH"
chmod +x scripts/check_commit_size.sh

echo "✅ Git pre-push hook installed at $HOOK_PATH"
echo "Commits will automatically be validated against the 200-line limit before pushing!"
