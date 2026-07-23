#!/usr/bin/env bash
#
# Weekly link-suggestion digest: reindexes the vault, calls suggest_links,
# filters out known template-noise clusters, and writes a reviewable digest
# for HeeGun -- never inserts anything itself (suggest-only, per
# specs/2026-07-20-link-suggestion-tool/SPEC.md G3/D1).
#
# Runs via launchd weekly (com.heegun.reports-link-digest) or manually:
#   ~/dev/reports-rag-mcp/weekly-link-digest.sh
#
set -euo pipefail

HOME_DIR="$HOME"
PROJ_DIR="$HOME_DIR/dev/reports-rag-mcp"
export PATH="$HOME_DIR/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
MODEL="claude-sonnet-5"

STAMP="$(date +%Y-%m-%d)"
LOG_DIR="$PROJ_DIR/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/link-digest-$STAMP.log"
DIGEST="$LOG_DIR/link-digest-$STAMP.md"
SEEN_FILE="$LOG_DIR/link-digest-seen-pairs.txt"
touch "$SEEN_FILE"

cd "$PROJ_DIR"

read -r -d '' PROMPT <<EOF || true
You are producing HeeGun's weekly link-suggestion digest for his personal
knowledge vault, unattended. Today's date: $STAMP.

STEPS:
1. Call the reports-rag MCP tool \`reindex()\` to make sure the index reflects
   any reports added this week.
2. Call \`suggest_links(top_k=40)\` to get candidate file pairs.
3. Filter out known template-noise clusters -- do NOT include a pair if
   either file matches these patterns (these are recurring/generated series,
   not meaningful conceptual connections): \`gtm-job-scans/*APPLY-TODAY*\`,
   \`gtm-job-scans/*OUTREACH*\`, any file inside a \`glossary/\` or
   \`glossary/audit-findings/\` directory. (Resume files are already excluded
   by the tool itself, per D7 -- no need to filter those again.)
4. Read $SEEN_FILE -- one "file_a|file_b" pair per line, pairs already shown
   in a prior digest. Skip any candidate whose pair (in either order) already
   appears there.
5. For whatever candidates remain after filtering, write a short digest to
   $DIGEST: a markdown list of "score | file_a <-> file_b", grouped loosely
   by folder/topic if that makes it easier to scan. If there's nothing new,
   write a one-line "no new candidates this week" file instead of an empty
   list.
6. Append every candidate pair you included in the digest (new ones only) to
   $SEEN_FILE as "file_a|file_b", one per line, so next week's run doesn't
   re-show the same ones. Do this whether or not HeeGun ends up accepting
   them -- "seen" means "already surfaced," not "already linked."

RULES:
- Do NOT insert any [[link]] into any file. This is a reviewable digest only
  -- HeeGun (or Claude, on his explicit per-suggestion instruction in a live
  session) does the actual inserting later. Never write to any .md file in
  the vault.
- Never stop to ask a question -- this is unattended. If reindex or
  suggest_links errors, write that error into the digest file so HeeGun sees
  it, and stop cleanly rather than guessing.
EOF

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
log "=== weekly link digest: $STAMP ==="

env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=1800000 \
  claude -p "$PROMPT" --model "$MODEL" --dangerously-skip-permissions \
  --name "_nest:link-digest" < /dev/null >> "$LOG" 2>&1

log "=== done. digest: $DIGEST ==="
