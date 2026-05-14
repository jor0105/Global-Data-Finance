#!/usr/bin/env bash
# Validates commit messages against a simplified Conventional Commits spec.
# Allowed types: feat, fix, refat, chore

MSG_FILE="${1:-.git/COMMIT_EDITMSG}"
MSG=$(head -1 "$MSG_FILE")

# Skip merge commits
if [[ "$MSG" =~ ^Merge\  ]]; then
  exit 0
fi

# Regex: type(scope): description
# Types: feat | fix | refat | chore
# Scope: optional, lowercase, allows &, /, _, -
# Description: required, no trailing period
PATTERN="^(feat|fix|refat|chore)(\([a-z0-9/&_-]+\))?:\ [a-z].{0,499}$"

if ! echo "$MSG" | grep -Eq "$PATTERN"; then
  echo ""
  echo "Commit message rejected. Use one of these formats:"
  echo ""
  echo "  feat(scope): description       - New feature"
  echo "  fix(scope): description        - Bug fix"
  echo "  refat(scope): description   - Code change, no behavior change"
  echo "  chore(scope): description      - Tooling, config, deps"
  echo ""
  echo "Rules:"
  echo "  - Scope is optional (lowercase, hyphens, and '&' allowed)"
  echo "  - Description starts lowercase"
  echo "  - Max 500 chars, no trailing period"
  echo ""
  echo "Examples:"
  echo "  feat(chat): add thinking mode toggle"
  echo "  fix(cvm): resolve 401 on insider endpoint"
  echo "  refat(backend): extract stock service"
  echo "  chore: update pre-commit hooks"
  echo ""
  echo "Your message: \"$MSG\""
  echo ""
  exit 1
fi
