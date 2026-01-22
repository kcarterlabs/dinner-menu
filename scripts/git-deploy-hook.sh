#!/bin/bash
# Git hook for automatic deployment on push
# Place this in .git/hooks/post-merge or set up with:
#   cp scripts/git-deploy-hook.sh .git/hooks/post-merge
#   chmod +x .git/hooks/post-merge

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🎣 Git Post-Merge Hook"
echo "======================"

# Load configuration
if [ -f "$PROJECT_ROOT/.deploy-config" ]; then
    source "$PROJECT_ROOT/.deploy-config"
fi

# Check if deployment should run
SKIP_DEPLOYMENT=false

# Check if only docs changed
if [ "${SKIP_ON_DOCS_ONLY:-true}" = "true" ]; then
    # Get list of changed files in the merge
    CHANGED_FILES=$(git diff-tree -r --name-only --no-commit-id ORIG_HEAD HEAD)
    
    # Check if all changes are in docs
    if echo "$CHANGED_FILES" | grep -qv '\.md$\|^docs/'; then
        echo "✅ Code changes detected, deployment will proceed"
    else
        echo "📚 Only documentation changed, skipping deployment"
        SKIP_DEPLOYMENT=true
    fi
fi

if [ "$SKIP_DEPLOYMENT" = "true" ]; then
    exit 0
fi

# Ask user if they want to deploy
echo ""
echo "New changes merged. Deploy now?"
echo "  1. Deploy now"
echo "  2. Skip (manual deployment later)"
read -p "Choice (1/2): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting automated deployment..."
        "$PROJECT_ROOT/scripts/auto-deploy.sh"
        ;;
    2)
        echo "Skipping deployment. Run './scripts/auto-deploy.sh' when ready."
        ;;
    *)
        echo "Invalid choice. Skipping deployment."
        ;;
esac
