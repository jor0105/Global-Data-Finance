#!/usr/bin/env python3
"""Portable sanity checker for git diffs to detect AI coding agent traps.

Detects common issues introduced on added/modified lines (+) in the staged
index or an explicit Git revision range:
  - Leftover debug statements (console methods, pause calls, debug tokens, raw output)
  - Stubbed implementations / unfulfilled placeholders (TODO throws, pass stubs)
  - Newly added type/lint bypass annotations

Inline linter bypass markers are always rejected; no allow annotation can
override that rule.

Fail-closed: Exits with code 2 on git errors, code 1 on violations, code 0 on clean pass.
Zero external dependencies (Python 3.10+ standard library only).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from git_changes import GitInspectionError, get_diff

_BREAKPOINT_WORD = 'breakpoint'
_DEBUGGER_WORD = 'debug' + 'ger'
_CONSOLE_WORD = 'console'
_PRINT_WORD = 'print'
_TS_DIRECTIVE_PREFIX = '@' + 'ts-'
_IGNORE_WORD = 'ignore'
_NOCHECK_WORD = 'nocheck'

DEBUG_PATTERNS = [
    (
        re.compile(r'\b' + _BREAKPOINT_WORD + r'\(\)'),
        _BREAKPOINT_WORD + '() call detected',
        False,
    ),
    (
        re.compile(r'\b' + _DEBUGGER_WORD + r';?'),
        _DEBUGGER_WORD + ' statement detected',
        False,
    ),
    (
        re.compile(r'\b' + _CONSOLE_WORD + r'\.(?:log|debug|trace|dir)\('),
        _CONSOLE_WORD + '.log/debug statement detected',
        False,
    ),
    (
        re.compile(r'(?<![a-zA-Z0-9_])' + _PRINT_WORD + r'\('),
        'raw '
        + _PRINT_WORD
        + '() call detected (use logger or allow in CLI files)',
        True,
    ),
]

STUB_PATTERNS = [
    (
        re.compile(r'throw\s+new\s+Error\(["\']TODO'),
        'TODO placeholder exception thrown',
    ),
    (
        re.compile(r'raise\s+NotImplementedError\(["\']TODO'),
        'TODO NotImplementedError thrown',
    ),
    (
        re.compile(r'pass\s*#\s*TODO', re.IGNORECASE),
        'pass TODO placeholder detected',
    ),
]

BYPASS_PATTERNS = [
    (
        re.compile(
            re.escape(_TS_DIRECTIVE_PREFIX)
            + r'(?:'
            + _IGNORE_WORD
            + '|'
            + _NOCHECK_WORD
            + r')\b'
        ),
        'TypeScript check bypass ('
        + _TS_DIRECTIVE_PREFIX
        + _IGNORE_WORD
        + '/'
        + _TS_DIRECTIVE_PREFIX
        + _NOCHECK_WORD
        + ') added',
    ),
    (
        re.compile(r'#\s*type:\s*' + _IGNORE_WORD + r'\b'),
        'Python type check bypass (# type: ' + _IGNORE_WORD + ') added',
    ),
    (
        re.compile(r'(?://|/\*)\s*eslint-disable(?:-next-line|-line)?\b'),
        'ESLint bypass comment added',
    ),
]

# Category-specific allow comments (require explicit reason content)
DEBUG_ALLOW_RE = re.compile(r'allow-debug:\s*\S+.*', re.IGNORECASE)
STUB_ALLOW_RE = re.compile(
    r'(?:allow-stub|stub-reason|todo-reason):\s*\S+.*', re.IGNORECASE
)
BYPASS_ALLOW_RE = re.compile(
    r'(?:allow-bypass|--\s*reason|#\s*reason):\s*\S+.*',
    re.IGNORECASE,
)
NOQA_PATTERN = re.compile(r'#\s*noqa\b', re.IGNORECASE)
NOQA_LABEL = '# ' + 'noqa'
NOQA_DESCRIPTION = f'Linter bypass ({NOQA_LABEL}) is never permitted'

NON_INSPECTABLE_EXTENSIONS = frozenset(
    {
        '.md',
        '.markdown',
        '.rst',
        '.txt',
        '.json',
        '.yaml',
        '.yml',
        '.toml',
        '.lock',
        '.csv',
        '.tsv',
        '.xml',
        '.svg',
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
        '.ico',
        '.map',
    }
)


def is_inspectable_file(file_path: str) -> bool:
    """Determine if a file is an authored source/script file to be checked."""
    p = Path(file_path)
    return p.suffix.lower() not in NON_INSPECTABLE_EXTENSIONS


def get_staged_diff(target_files: list[str] | None = None) -> str:
    """Retrieve the staged diff for compatibility with direct script callers."""
    return get_diff(context_lines=0, target_files=target_files)


def is_cli_or_script_file(file_path: str) -> bool:
    """Determine if file is a CLI entry point or script where print is expected."""
    p = Path(file_path)
    posix_path = p.as_posix().lower()
    return (
        '/cli/' in posix_path
        or '/scripts/' in posix_path
        or posix_path.startswith('scripts/')
        or p.name in ('manage.py', 'cli.py', 'main.py')
    )


def _check_debug_violations(
    content: str, file_path: str, line_num: int, allow_debug_in_scripts: bool
) -> list[str]:
    errors: list[str] = []
    is_script = is_cli_or_script_file(file_path)
    for pattern, desc, is_print_pattern in DEBUG_PATTERNS:
        if is_print_pattern and allow_debug_in_scripts and is_script:
            continue
        if pattern.search(content) and not DEBUG_ALLOW_RE.search(content):
            errors.append(f'{file_path}:{line_num}: [DEBUG] {desc}')
    return errors


def _check_stub_violations(
    content: str, file_path: str, line_num: int
) -> list[str]:
    errors: list[str] = []
    for pattern, desc in STUB_PATTERNS:
        if pattern.search(content) and not STUB_ALLOW_RE.search(content):
            errors.append(f'{file_path}:{line_num}: [STUB] {desc}')
    return errors


def _check_bypass_violations(
    content: str, file_path: str, line_num: int
) -> list[str]:
    errors: list[str] = []
    for pattern, desc in BYPASS_PATTERNS:
        if pattern.search(content) and not BYPASS_ALLOW_RE.search(content):
            errors.append(f'{file_path}:{line_num}: [BYPASS] {desc}')
    return errors


def _check_noqa_violations(
    content: str, file_path: str, line_num: int
) -> list[str]:
    """Reject inline noqa independently of the other bypass policies."""
    if not NOQA_PATTERN.search(content):
        return []
    return [
        f'{file_path}:{line_num}: [BYPASS] {NOQA_DESCRIPTION}',
    ]


def scan_diff(
    diff_text: str,
    allow_debug_in_scripts: bool = True,
    check_bypasses: bool = True,
) -> list[str]:
    """Scan added diff lines for violations and return formatted error messages."""
    errors: list[str] = []
    current_file = ''
    line_num = 0

    for line in diff_text.splitlines():
        if line.startswith('+++ b/'):
            current_file = line[6:]
            continue
        if line.startswith('@@ '):
            m = re.search(r'\+(\d+)', line)
            if m:
                line_num = int(m.group(1)) - 1
            continue

        if not line.startswith('+') or line.startswith('+++'):
            continue

        if not is_inspectable_file(current_file):
            continue

        line_num += 1
        added_content = line[1:].strip()
        if not added_content:
            continue

        errors.extend(
            _check_debug_violations(
                added_content, current_file, line_num, allow_debug_in_scripts
            )
        )
        errors.extend(
            _check_stub_violations(added_content, current_file, line_num)
        )
        errors.extend(
            _check_noqa_violations(added_content, current_file, line_num)
        )
        if check_bypasses:
            errors.extend(
                _check_bypass_violations(added_content, current_file, line_num)
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'files',
        nargs='*',
        help='Specific files to check. If omitted, checks all staged files.',
    )
    parser.add_argument(
        '--disallow-script-prints',
        action='store_true',
        help='Fail on print() even inside scripts/ or cli/ directories.',
    )
    parser.add_argument(
        '--range',
        dest='revision_range',
        help='Inspect an explicit Git A..B or A...B range instead of the index.',
    )
    args = parser.parse_args()
    if args.files and args.revision_range:
        parser.error('files cannot be combined with --range')

    try:
        diff_text = get_diff(
            context_lines=0,
            target_files=args.files if args.files else None,
            revision_range=args.revision_range,
        )
    except GitInspectionError as err:
        sys.stderr.write(
            f'ERROR [DIFF_SANITY]: unable to inspect Git changes: {err}\n'
        )
        return 2

    if not diff_text.strip():
        scope = 'revision range' if args.revision_range else 'staged diff'
        sys.stdout.write(
            f'SKIP [DIFF_SANITY]: No {scope} additions to inspect.\n'
        )
        return 0

    errors = scan_diff(
        diff_text,
        allow_debug_in_scripts=not args.disallow_script_prints,
        check_bypasses=True,
    )

    if errors:
        sys.stderr.write(
            'FAIL [DIFF_SANITY]: Potential AI agent artifacts detected in Git diff:\n'
        )
        for error_msg in errors:
            sys.stderr.write(f'  • {error_msg}\n')
        sys.stderr.write(
            '\nResolution: Fix the code, use the appropriate file/scope, or '
            'configure the lint rule explicitly for that file. '
            f'{NOQA_LABEL} is never permitted; other annotations require a '
            'specific reason '
            '("allow-debug", "allow-stub", or "-- reason: <why>").\n'
        )
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
