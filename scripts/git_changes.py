#!/usr/bin/env python3
"""Read staged Git changes and revision ranges for local quality gates."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitInspectionError(RuntimeError):
    """Raised when a required Git inspection cannot be completed."""


def _run_git(
    arguments: list[str],
    root: Path,
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run Git in a repository and translate infrastructure failures."""
    try:
        return subprocess.run(
            ['git', *arguments],
            cwd=root,
            capture_output=True,
            check=check,
            encoding='utf-8',
            text=True,
        )
    except (
        subprocess.SubprocessError,
        FileNotFoundError,
        OSError,
        UnicodeError,
    ) as err:
        detail = getattr(err, 'stderr', None) or str(err)
        raise GitInspectionError(str(detail).strip()) from err


def _root(repo_root: Path | None) -> Path:
    """Return the supplied repository root or the current working directory."""
    return repo_root or Path.cwd()


def range_target_revision(
    revision_range: str, repo_root: Path | None = None
) -> str:
    """Validate a Git range and return the revision representing its right side."""
    separator = '...' if '...' in revision_range else '..'
    if separator not in revision_range:
        raise GitInspectionError(
            'revision range must use the Git A..B or A...B notation'
        )
    _, _, target = revision_range.rpartition(separator)
    if not target:
        raise GitInspectionError(
            'revision range must include an ending revision'
        )

    result = _run_git(
        ['rev-parse', '--verify', f'{target}^{{commit}}'], _root(repo_root)
    )
    return result.stdout.strip()


def get_diff(
    *,
    context_lines: int,
    target_files: list[str] | None = None,
    revision_range: str | None = None,
    no_renames: bool = False,
    repo_root: Path | None = None,
) -> str:
    """Return a unified diff from the index or an explicit revision range."""
    root = _root(repo_root)
    command = ['diff', '--no-color', f'-U{context_lines}']
    if no_renames:
        command.append('--no-renames')
    if revision_range is None:
        command.append('--cached')
    else:
        range_target_revision(revision_range, root)
        command.append(revision_range)
    command.append('--')
    if target_files:
        command.extend(target_files)
    return _run_git(command, root).stdout


def get_changed_paths(
    *,
    revision_range: str | None = None,
    diff_filter: str = 'ACMR',
    repo_root: Path | None = None,
) -> list[str]:
    """Return paths added, copied, modified, or renamed in a Git comparison."""
    root = _root(repo_root)
    command = [
        'diff',
        '--no-color',
        '--name-only',
        f'--diff-filter={diff_filter}',
    ]
    if revision_range is None:
        command.append('--cached')
    else:
        range_target_revision(revision_range, root)
        command.append(revision_range)
    command.append('--')
    return sorted(
        path for path in _run_git(command, root).stdout.splitlines() if path
    )


def read_git_file(
    file_path: str,
    *,
    revision_range: str | None = None,
    repo_root: Path | None = None,
) -> str | None:
    """Read a file from the staged index or from a revision range endpoint."""
    root = _root(repo_root)
    if revision_range is None:
        index_entry = _run_git(['ls-files', '--stage', '--', file_path], root)
        if not index_entry.stdout.strip():
            return None
        object_name = f':{file_path}'
    else:
        target = range_target_revision(revision_range, root)
        object_name = f'{target}:{file_path}'
        exists = _run_git(['cat-file', '-e', object_name], root, check=False)
        if exists.returncode != 0:
            return None

    return _run_git(['show', object_name], root).stdout
