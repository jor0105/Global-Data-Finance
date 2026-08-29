#!/usr/bin/env python3
"""Detect weakened, skipped, or deleted tests in staged or ranged Git diffs.

Detects common test erosion patterns:
  - Focused/isolated tests (.only, fit, fdescribe) - strictly prohibited
  - Skipped or xfailed tests (@pytest.mark.skip, it.skip, xit) - fail unless
    justified with a reason
  - Unjustified net removal of assertion lines in test files
  - Deleted test files without staged policy authorization
    (.test-deletions.json)

Fail-closed: Exits with code 2 on git errors, code 1 on violations, and code 0
on a clean pass.
Zero external dependencies (Python 3.10+ standard library only).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from git_changes import GitInspectionError, get_diff, read_git_file

# Focused tests are strictly prohibited in pre-commit (no bypass allowed)
STRICT_FOCUS_PATTERNS = [
    (
        re.compile(r'\b(?:it|describe|test)\.only\b'),
        'Focused test (.only) detected (strictly prohibited in pre-commit)',
    ),
    (
        re.compile(r'\b(?:fit|fdescribe)\('),
        'Focused test (fit/fdescribe) detected '
        '(strictly prohibited in pre-commit)',
    ),
]

SKIPPED_TEST_PATTERNS = [
    (
        re.compile(r'@pytest\.mark\.(?:skip|xfail)\b'),
        'Skipped/xfailed pytest marker added',
    ),
    (
        re.compile(r'\b(?:it|describe|test)\.skip\b'),
        'Skipped test (.skip) detected',
    ),
    (re.compile(r'\b(?:xit|xtest)\('), 'Skipped test (xit/xtest) detected'),
]

ASSERTION_PATTERNS = re.compile(
    r'\b(?:assert\s+|expect\(|self\.assert|assert_that\b|t\.assert|'
    r'assertIs|assertEqual|assertTrue|assertFalse|pytest\.(?:raises|warns)\()'
)

# Must include a colon and non-empty reason content
ALLOW_SKIP_RE = re.compile(
    r'(?:allow-skip|skip-reason):\s*\S+.*', re.IGNORECASE
)
ALLOW_ASSERTION_REDUCTION_RE = re.compile(
    r'(?:allow-assertion-reduction|assertion-reduction-reason):\s*\S+.*',
    re.IGNORECASE,
)
_ALLOW_DELETED_FLAG = '--allow-' + 'deleted-tests'


def is_test_file(file_path: str) -> bool:
    """Check if the given file path belongs to a test suite."""
    p = Path(file_path)
    name = p.name.lower()
    posix_path = p.as_posix().lower()
    return (
        name.startswith('test_')
        or name.endswith(
            (
                '_test.py',
                '.test.ts',
                '.test.js',
                '.test.tsx',
                '.test.jsx',
                '.spec.ts',
                '.spec.js',
                '.spec.tsx',
                '.spec.jsx',
            )
        )
        or '/tests/' in posix_path
        or '/__tests__/' in posix_path
        or posix_path.startswith(('tests/', 'test/'))
    )


def read_staged_git_file(
    file_path: str, repo_root: Path | None = None
) -> str | None:
    """Read an indexed file, returning ``None`` only when it is absent."""
    return read_git_file(file_path, repo_root=repo_root)


def is_test_deletion_approved(
    file_path: str,
    repo_root: Path | None = None,
    revision_range: str | None = None,
) -> bool:
    """Check whether a test deletion has approval in inspected Git state."""
    policy_names = ('.test-deletions.json', '.test-integrity-policy.json')
    for policy_name in policy_names:
        content = read_git_file(
            policy_name,
            repo_root=repo_root,
            revision_range=revision_range,
        )
        if content is not None:
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    allowed = data.get('allowed_deletions')
                    if isinstance(allowed, dict) and file_path in allowed:
                        reason = allowed[file_path]
                        if isinstance(reason, str) and reason.strip():
                            return True
                        if (
                            isinstance(reason, dict)
                            and str(reason.get('reason', '')).strip()
                        ):
                            return True
            except (OSError, json.JSONDecodeError):
                pass
    return False


def get_staged_diff(target_files: list[str] | None = None) -> str:
    """Retrieve a non-renamed staged diff for direct script callers."""
    return get_diff(
        context_lines=1,
        target_files=target_files,
        no_renames=True,
    )


def _evaluate_file_assertions(
    file_path: str,
    removed_assertions: int,
    added_assertions: int,
    has_reduction_allow: bool,
    is_deleted: bool,
    allow_deleted: bool,
    repo_root: Path | None = None,
    revision_range: str | None = None,
) -> list[str]:
    """Evaluate whether changes to a test file violate integrity."""
    errors: list[str] = []
    if not (file_path and is_test_file(file_path)):
        return errors

    if is_deleted:
        if not (
            allow_deleted
            or is_test_deletion_approved(
                file_path,
                repo_root,
                revision_range,
            )
        ):
            errors.append(
                f'{file_path}: [TEST_DELETION] Test file deleted in staged '
                f'changes. To authorize, pass {_ALLOW_DELETED_FLAG} '
                'or stage a policy entry in .test-deletions.json.'
            )
    elif removed_assertions > added_assertions and not has_reduction_allow:
        errors.append(
            f'{file_path}: [TEST_INTEGRITY] Net reduction of test assertions '
            f'detected ({removed_assertions} removed vs {added_assertions} '
            'added without '
            f'"allow-assertion-reduction: <reason>")'
        )
    return errors


def _check_focus_or_skip_line(
    content: str, file_path: str, line_num: int
) -> list[str]:
    """Check an added line for focus or skip markers."""
    errors: list[str] = []
    for pattern, desc in STRICT_FOCUS_PATTERNS:
        if pattern.search(content):
            errors.append(
                f'{file_path}:{line_num}: [TEST_FOCUS] {desc} ("{content}")'
            )

    for pattern, desc in SKIPPED_TEST_PATTERNS:
        if pattern.search(content) and not ALLOW_SKIP_RE.search(content):
            errors.append(
                f'{file_path}:{line_num}: [TEST_SKIP] {desc} ("{content}")'
            )

    return errors


class _FileDiffState:
    """Track assertion and skip counts for a file during diff scanning."""

    def __init__(self) -> None:
        self.current_file: str = ''
        self.prev_file: str = ''
        self.line_num: int = 0
        self.removed_assertions: int = 0
        self.added_assertions: int = 0
        self.has_assertion_reduction_allow: bool = False
        self.is_deleted_file: bool = False

    def reset_for_file(self, file_path: str, is_deleted: bool = False) -> None:
        self.current_file = file_path
        self.removed_assertions = 0
        self.added_assertions = 0
        self.has_assertion_reduction_allow = False
        self.is_deleted_file = is_deleted

    def evaluate(
        self,
        allow_deleted: bool,
        repo_root: Path | None = None,
        revision_range: str | None = None,
    ) -> list[str]:
        return _evaluate_file_assertions(
            self.current_file,
            self.removed_assertions,
            self.added_assertions,
            self.has_assertion_reduction_allow,
            self.is_deleted_file,
            allow_deleted,
            repo_root,
            revision_range,
        )

    def track_previous_file(self, line: str) -> bool:
        """Record an old-file header and report whether it was consumed."""
        if not line.startswith('--- a/'):
            return False
        self.prev_file = line[6:]
        return True

    def handle_file_start(
        self,
        line: str,
        allow_deleted: bool,
        repo_root: Path | None,
        revision_range: str | None,
    ) -> list[str] | None:
        """Finish the prior file and initialize a new or deleted file."""
        if line.startswith('+++ b/'):
            errors = self.evaluate(allow_deleted, repo_root, revision_range)
            self.reset_for_file(line[6:], is_deleted=False)
            return errors
        if line.startswith('+++ /dev/null'):
            errors = self.evaluate(allow_deleted, repo_root, revision_range)
            self.reset_for_file(self.prev_file, is_deleted=True)
            return errors
        return None

    def handle_hunk(self, line: str) -> bool:
        """Initialize the added-side line number from a hunk header."""
        if not line.startswith('@@ '):
            return False
        match = re.search(r'\+(\d+)', line)
        if match:
            self.line_num = int(match.group(1)) - 1
        return True

    def handle_removal(self, line: str) -> bool:
        """Count an assertion removed from the current test file."""
        if not line.startswith('-') or line.startswith('---'):
            return False
        if ASSERTION_PATTERNS.search(line[1:].strip()):
            self.removed_assertions += 1
        return True

    def handle_addition(self, line: str) -> list[str] | None:
        """Inspect and count an added line from the current test file."""
        if not line.startswith('+') or line.startswith('+++'):
            return None
        self.line_num += 1
        content = line[1:].strip()
        if not content:
            return []
        if ALLOW_ASSERTION_REDUCTION_RE.search(content):
            self.has_assertion_reduction_allow = True
        if ASSERTION_PATTERNS.search(content):
            self.added_assertions += 1
        return _check_focus_or_skip_line(
            content, self.current_file, self.line_num
        )

    def inspect_test_line(self, line: str) -> list[str]:
        """Dispatch one diff line for the active test file."""
        if self.handle_hunk(line) or self.handle_removal(line):
            return []
        return self.handle_addition(line) or []


def scan_test_integrity(
    diff_text: str,
    allow_deleted: bool = False,
    repo_root: Path | None = None,
    revision_range: str | None = None,
) -> list[str]:
    """Scan diff for test integrity violations."""
    errors: list[str] = []
    state = _FileDiffState()

    for line in diff_text.splitlines():
        if state.track_previous_file(line):
            continue

        file_errors = state.handle_file_start(
            line, allow_deleted, repo_root, revision_range
        )
        if file_errors is not None:
            errors.extend(file_errors)
            continue

        if is_test_file(state.current_file):
            errors.extend(state.inspect_test_line(line))

    errors.extend(state.evaluate(allow_deleted, repo_root, revision_range))
    return errors


def main() -> int:
    """Validate that test changes retain required executable assertions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'files',
        nargs='*',
        help=(
            'Specific files to check. If omitted, checks all staged test '
            'files.'
        ),
    )
    parser.add_argument(
        _ALLOW_DELETED_FLAG,
        dest='allow_deleted',
        action='store_true',
        help='Allow test file deletions without failing the gate.',
    )
    parser.add_argument(
        '--range',
        dest='revision_range',
        help=(
            'Inspect an explicit Git A..B or A...B range instead of the index.'
        ),
    )
    args = parser.parse_args()
    if args.files and args.revision_range:
        parser.error('files cannot be combined with --range')

    try:
        diff_text = get_diff(
            context_lines=1,
            target_files=args.files if args.files else None,
            revision_range=args.revision_range,
            no_renames=True,
        )
        if not diff_text.strip():
            scope = 'revision range' if args.revision_range else 'staged test'
            sys.stdout.write(
                f'SKIP [TEST_INTEGRITY]: No {scope} changes to inspect.\n'
            )
            return 0
        errors = scan_test_integrity(
            diff_text,
            allow_deleted=args.allow_deleted,
            revision_range=args.revision_range,
        )
    except GitInspectionError as err:
        sys.stderr.write(
            f'ERROR [TEST_INTEGRITY]: unable to inspect Git changes: {err}\n'
        )
        return 2

    if errors:
        sys.stderr.write(
            'FAIL [TEST_INTEGRITY]: Test integrity violations detected in '
            'Git diff:\n'
        )
        for error_msg in errors:
            sys.stderr.write(f'  • {error_msg}\n')
        sys.stderr.write(
            '\nResolution: Restore assertions, remove .only/fit markers, or '
            'justify with '
            '"allow-assertion-reduction: <reason>" / "allow-skip: <reason>".\n'
        )
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
