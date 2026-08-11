#!/usr/bin/env bash
# Fail the commit when the generated harness mirrors drift from the .agents
# source of truth. .agents/ is canonical; .claude, .github, .codex and
# opencode.json are generated. Run the printed fix command (without
# --check) and re-stage when this hook fails.
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT" || exit 1

# .agents/ and every mirror it generates are gitignored, so a fresh clone --
# CI, a new machine, a release runner -- has no harness to compare. Mirror
# sync is a local-only guarantee by construction; skipping is the honest
# outcome, not a silent pass, so say so and exit clean.
if [ ! -d ".agents/scripts" ]; then
  echo "  - harness sync skipped: .agents/ not present (untracked by design)" >&2
  exit 0
fi

fail=0

run_check() {
  local label="$1" script="$2"

  if [ ! -f "$script" ]; then
    echo "  x ${label}  ->  missing script: ${script}" >&2
    fail=1
    return
  fi

  local output status=0
  output="$(python3 "$script" --check 2>&1)" || status=$?
  [ "$status" -eq 0 ] && return

  echo "  x ${label}  ->  fix: python3 ${script}" >&2
  # Never swallow the reason. A crashing script and a genuinely drifted
  # mirror both exit non-zero, and only this output tells them apart --
  # discarding it turns "the harness is broken" into "regenerate the
  # mirrors", which is the wrong fix and never converges.
  if [ -n "$output" ]; then
    printf '%s\n' "$output" | head -n 20 | while IFS= read -r line; do
      echo "      | ${line}" >&2
    done
  fi
  fail=1
}

echo "Checking harness mirror sync (.agents = source of truth)..." >&2
run_check "agent mirrors (claude/github/codex/opencode)" \
  ".agents/scripts/sync-config-agents.py"
run_check "workflow mirrors (github/opencode/claude commands)" \
  ".agents/scripts/sync-workflows.py"
run_check "skill index (.agents/skill-index.md)" \
  ".agents/scripts/generate-skill-index.py"

if [ "$fail" -ne 0 ]; then
  echo "" >&2
  echo "Harness mirrors drifted from .agents. Run the fix command(s) above and re-stage." >&2
  exit 1
fi

echo "  ok harness mirrors in sync" >&2
