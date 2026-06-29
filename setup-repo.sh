#!/usr/bin/env bash
# One-shot: turn this folder into a git repo with a clean first commit.
# Run this AFTER your toolchain is fixed:
#   sudo rm -rf /Library/Developer/CommandLineTools && xcode-select --install
# Then verify: git --version
set -euo pipefail
cd "$(dirname "$0")"

# Sanity check: git must actually run (not the broken xcrun stub)
if ! git --version >/dev/null 2>&1; then
  echo "git is not working yet. Fix Command Line Tools first:"
  echo "  sudo rm -rf /Library/Developer/CommandLineTools && xcode-select --install"
  exit 1
fi

git init
git add .
git commit -m "Initial commit: GTM engineering portfolio (attribution engine)"

cat <<'EOF'

Local repo created with a first commit.

Next, push to GitHub (replace USER/REPO):
  1. Create an empty repo on github.com (start it PRIVATE).
  2. git remote add origin git@github.com:USER/REPO.git
  3. git branch -M main
  4. git push -u origin main

Before flipping the repo to public, re-scan for anything sensitive:
  - customer names, real contact names
  - account IDs / customer IDs
  - API keys or tokens
EOF
