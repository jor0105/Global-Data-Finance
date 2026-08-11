#!/usr/bin/env bash
# Validates commit messages against a simplified Conventional Commits spec.
# Allowed types: feat, fix, refactor, chore, docs, test, build, ci, perf, revert

MSG_FILE="${1:-.git/COMMIT_EDITMSG}"
MSG=$(head -1 "$MSG_FILE")

# Skip merge commits and rebase helper commits (fixup!/squash!/amend!)
if [[ "$MSG" =~ ^Merge\  ]] || [[ "$MSG" =~ ^(fixup|squash|amend)! ]]; then
  exit 0
fi

# Regex: type(scope)!: description
# Types: feat | fix | refactor | chore | docs | test | build | ci | perf | revert
# Scope: optional, lowercase, allows &, /, _, -
# `!`: optional breaking-change marker
# Description: required, starts lowercase, no trailing period
TYPES="feat|fix|refactor|chore|docs|test|build|ci|perf|revert"
PATTERN="^(${TYPES})(\([a-z0-9/&_-]+\))?!?:\ [a-z].{0,499}[^.]$"

if ! echo "$MSG" | grep -Eq "$PATTERN"; then
  echo ""
  echo "Commit message rejected. Use one of these formats:"
  echo ""
  echo "  feat(scope): description     - New feature"
  echo "  fix(scope): description      - Bug fix"
  echo "  refactor(scope): description - Code change, no behavior change"
  echo "  chore(scope): description    - Tooling, config, deps"
  echo "  docs | test | build | ci | perf | revert"
  echo ""
  echo "Rules:"
  echo "  - Scope is optional (lowercase, hyphens, and '&' allowed)"
  echo "  - Append '!' before ':' to flag a breaking change"
  echo "  - Description starts lowercase"
  echo "  - Max 500 chars, no trailing period"
  echo ""
  echo "Examples:"
  echo "  feat(chat): add thinking mode toggle"
  echo "  fix(cvm): resolve 401 on insider endpoint"
  echo "  refactor(backend): extract stock service"
  echo "  feat(api)!: drop legacy loader entrypoint"
  echo "  chore: update pre-commit hooks"
  echo ""
  echo "Your message: \"$MSG\""
  echo ""
  exit 1
fi
