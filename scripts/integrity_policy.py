"""Read and validate test-deletion policy entries in Git state."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

from scripts.git_changes import read_git_file

_POLICY_NAMES = ('.test-deletions.json', '.test-integrity-policy.json')
_DELETED_FILE_RE = re.compile(r'(?m)^--- a/(.+)\n\+\+\+ /dev/null(?:\n|$)')


def read_policy_entries(
    policy_name: str,
    repo_root: Path | None = None,
    revision_range: str | None = None,
) -> dict[str, object]:
    """Read one policy's deletion entries from the inspected Git state."""
    content = read_git_file(
        policy_name, repo_root=repo_root, revision_range=revision_range
    )
    if content is None:
        return {}
    try:
        data = json.loads(content)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    allowed = data.get('allowed_deletions')
    if not isinstance(allowed, dict):
        return {}
    return {str(path): reason for path, reason in allowed.items()}


def stale_deletion_policy_errors(
    diff_text: str,
    is_test_file: Callable[[str], bool],
    repo_root: Path | None = None,
    revision_range: str | None = None,
) -> list[str]:
    """Return diagnostics for policy entries absent from this diff."""
    deleted_paths = {
        match.group(1)
        for match in _DELETED_FILE_RE.finditer(diff_text)
        if is_test_file(match.group(1))
    }
    errors: list[str] = []
    for policy_name in _POLICY_NAMES:
        allowed = read_policy_entries(
            policy_name, repo_root=repo_root, revision_range=revision_range
        )
        for file_path in allowed:
            if file_path not in deleted_paths:
                errors.append(
                    f'{policy_name}: [TEST_POLICY] stale deletion '
                    f'authorization for {file_path!r}; remove it or delete '
                    'that test in the inspected Git diff.'
                )
    return errors
