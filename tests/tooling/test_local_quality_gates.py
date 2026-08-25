"""Regression tests for repository-local quality gate entry points."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).parents[2]
DIFF_SANITY = REPOSITORY_ROOT / 'scripts' / 'check_diff_sanity.py'
TEST_INTEGRITY = REPOSITORY_ROOT / 'scripts' / 'check_test_integrity.py'
LOCKFILE_SYNC = REPOSITORY_ROOT / 'scripts' / 'check_lockfile_sync.py'
SHELL_SYNTAX = REPOSITORY_ROOT / 'scripts' / 'check-shell-syntax.py'


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a Git command in an isolated test repository."""
    return subprocess.run(
        ['git', *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def initialize_git_repository(repo: Path) -> None:
    """Initialize a disposable repository with deterministic commit metadata."""
    run_git(repo, 'init', '--quiet')
    run_git(repo, 'config', 'user.name', 'Quality Gate Tests')
    run_git(repo, 'config', 'user.email', 'quality-gates@example.invalid')


def run_gate(
    script: Path, repo: Path, *arguments: str
) -> subprocess.CompletedProcess[str]:
    """Execute a gate script from an isolated repository."""
    return subprocess.run(
        [sys.executable, str(script), *arguments],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def test_diff_sanity_rejects_new_debug_artifacts(tmp_path: Path) -> None:
    """The diff gate must reject debug calls added to authored Python code."""
    initialize_git_repository(tmp_path)
    source = tmp_path / 'src' / 'example.py'
    source.parent.mkdir()
    debug_call = 'breakpoint' + '()'
    source.write_text(
        f'def example() -> None:\n    {debug_call}\n', encoding='utf-8'
    )
    run_git(tmp_path, 'add', '--', 'src/example.py')

    result = run_gate(DIFF_SANITY, tmp_path)

    assert result.returncode == 1
    assert '[DEBUG]' in result.stderr
    assert 'breakpoint' in result.stderr


def test_diff_sanity_does_not_flag_its_detector_source(tmp_path: Path) -> None:
    """The detector must not reject its own encoded rule definitions."""
    initialize_git_repository(tmp_path)
    source = tmp_path / 'scripts' / 'check_diff_sanity.py'
    source.parent.mkdir()
    source.write_text(
        DIFF_SANITY.read_text(encoding='utf-8'), encoding='utf-8'
    )
    run_git(tmp_path, 'add', '--', 'scripts/check_diff_sanity.py')

    result = run_gate(DIFF_SANITY, tmp_path)

    assert result.returncode == 0, result.stderr


def test_diff_sanity_requires_a_non_empty_bypass_reason(
    tmp_path: Path,
) -> None:
    """An empty bypass annotation must not authorize a type-check suppression."""
    initialize_git_repository(tmp_path)
    source = tmp_path / 'src' / 'example.py'
    source.parent.mkdir()
    type_ignore = '# type: ' + 'ignore'
    empty_reason = 'allow-' + 'bypass:'
    source.write_text(
        f'value = missing  {type_ignore}[name]  # {empty_reason}\n',
        encoding='utf-8',
    )
    run_git(tmp_path, 'add', '--', 'src/example.py')

    result = run_gate(DIFF_SANITY, tmp_path)

    assert result.returncode == 1
    assert '[BYPASS]' in result.stderr


def test_diff_sanity_never_allows_noqa(tmp_path: Path) -> None:
    """A linter suppression remains rejected even with a stated rationale."""
    initialize_git_repository(tmp_path)
    source = tmp_path / 'src' / 'example.py'
    source.parent.mkdir()
    noqa_marker = '# ' + 'noqa'
    bypass_reason = 'allow-' + 'bypass: reviewed exception'
    source.write_text(
        f'import unused  {noqa_marker}: F401  # {bypass_reason}\n',
        encoding='utf-8',
    )
    run_git(tmp_path, 'add', '--', 'src/example.py')

    result = run_gate(DIFF_SANITY, tmp_path)

    assert result.returncode == 1
    assert '[BYPASS]' in result.stderr


def test_diff_sanity_scans_an_explicit_commit_range(tmp_path: Path) -> None:
    """The CI range mode must detect a violation after the index is empty."""
    initialize_git_repository(tmp_path)
    source = tmp_path / 'src' / 'example.py'
    source.parent.mkdir()
    source.write_text(
        'def example() -> None:\n    return None\n', encoding='utf-8'
    )
    run_git(tmp_path, 'add', '--', 'src/example.py')
    run_git(tmp_path, 'commit', '--quiet', '-m', 'baseline')

    debug_call = 'breakpoint' + '()'
    source.write_text(
        f'def example() -> None:\n    {debug_call}\n', encoding='utf-8'
    )
    run_git(tmp_path, 'add', '--', 'src/example.py')
    run_git(tmp_path, 'commit', '--quiet', '-m', 'add debug artifact')

    result = run_gate(DIFF_SANITY, tmp_path, '--range', 'HEAD~1...HEAD')

    assert result.returncode == 1
    assert '[DEBUG]' in result.stderr


def test_test_integrity_rejects_focus_skip_and_assertion_reduction(
    tmp_path: Path,
) -> None:
    """The test gate must detect weakened and focused tests in one diff."""
    initialize_git_repository(tmp_path)
    test_file = tmp_path / 'tests' / 'test_example.py'
    test_file.parent.mkdir()
    original = (
        'def test_example() -> None:\n    assert 1 == 1\n    assert 2 == 2\n'
    )
    test_file.write_text(original, encoding='utf-8')
    run_git(tmp_path, 'add', '--', 'tests/test_example.py')
    run_git(tmp_path, 'commit', '--quiet', '-m', 'baseline')

    focused_test = 'test' + '.only'
    skipped_marker = '@pytest.mark.' + 'skip'
    weakened = (
        'def test_example() -> None:\n'
        '    assert 1 == 1\n'
        f'    {focused_test}("example")\n'
        f'    {skipped_marker}\n'
    )
    test_file.write_text(weakened, encoding='utf-8')
    run_git(tmp_path, 'add', '--', 'tests/test_example.py')

    result = run_gate(TEST_INTEGRITY, tmp_path)

    assert result.returncode == 1
    assert '[TEST_FOCUS]' in result.stderr
    assert '[TEST_SKIP]' in result.stderr
    assert '[TEST_INTEGRITY]' in result.stderr


def test_test_integrity_rejects_pytest_context_assertion_removal(
    tmp_path: Path,
) -> None:
    """Removing a pytest exception assertion must be treated as test erosion."""
    initialize_git_repository(tmp_path)
    test_file = tmp_path / 'tests' / 'test_example.py'
    test_file.parent.mkdir()
    test_file.write_text(
        'import pytest\n\n'
        'def test_error() -> None:\n'
        '    with pytest.raises(ValueError):\n'
        '        raise ValueError("expected")\n',
        encoding='utf-8',
    )
    run_git(tmp_path, 'add', '--', 'tests/test_example.py')
    run_git(tmp_path, 'commit', '--quiet', '-m', 'baseline')

    test_file.write_text(
        'def test_error() -> None:\n    raise ValueError("expected")\n',
        encoding='utf-8',
    )
    run_git(tmp_path, 'add', '--', 'tests/test_example.py')

    result = run_gate(TEST_INTEGRITY, tmp_path)

    assert result.returncode == 1
    assert '[TEST_INTEGRITY]' in result.stderr


def test_test_integrity_rejects_a_test_renamed_outside_test_scope(
    tmp_path: Path,
) -> None:
    """Rename detection must model a test moved into production code as deletion."""
    initialize_git_repository(tmp_path)
    test_file = tmp_path / 'tests' / 'test_security.py'
    test_file.parent.mkdir()
    test_file.write_text(
        'def test_security() -> None:\n    assert True\n', encoding='utf-8'
    )
    run_git(tmp_path, 'add', '--', 'tests/test_security.py')
    run_git(tmp_path, 'commit', '--quiet', '-m', 'baseline')

    retired_file = tmp_path / 'src' / 'retired_test.py'
    retired_file.parent.mkdir()
    run_git(tmp_path, 'mv', 'tests/test_security.py', 'src/retired_test.py')

    result = run_gate(TEST_INTEGRITY, tmp_path)

    assert result.returncode == 1
    assert '[TEST_DELETION]' in result.stderr


def test_test_integrity_scans_a_rename_in_an_explicit_range(
    tmp_path: Path,
) -> None:
    """The CI range mode must retain the same rename-to-deletion protection."""
    initialize_git_repository(tmp_path)
    test_file = tmp_path / 'tests' / 'test_security.py'
    test_file.parent.mkdir()
    test_file.write_text(
        'def test_security() -> None:\n    assert True\n', encoding='utf-8'
    )
    run_git(tmp_path, 'add', '--', 'tests/test_security.py')
    run_git(tmp_path, 'commit', '--quiet', '-m', 'baseline')

    retired_file = tmp_path / 'src' / 'retired_test.py'
    retired_file.parent.mkdir()
    run_git(tmp_path, 'mv', 'tests/test_security.py', 'src/retired_test.py')
    run_git(tmp_path, 'commit', '--quiet', '-m', 'retire test')

    result = run_gate(TEST_INTEGRITY, tmp_path, '--range', 'HEAD~1...HEAD')

    assert result.returncode == 1
    assert '[TEST_DELETION]' in result.stderr


def test_test_integrity_requires_authorization_for_deleted_tests(
    tmp_path: Path,
) -> None:
    """The test gate must require a staged reason for deleting test files."""
    initialize_git_repository(tmp_path)
    test_file = tmp_path / 'tests' / 'test_removed.py'
    test_file.parent.mkdir()
    test_file.write_text(
        'def test_removed() -> None:\n    assert True\n', encoding='utf-8'
    )
    run_git(tmp_path, 'add', '--', 'tests/test_removed.py')
    run_git(tmp_path, 'commit', '--quiet', '-m', 'baseline')

    test_file.unlink()
    run_git(tmp_path, 'add', '--update')
    denied = run_gate(TEST_INTEGRITY, tmp_path)
    assert denied.returncode == 1
    assert '[TEST_DELETION]' in denied.stderr

    policy = {
        'allowed_deletions': {
            'tests/test_removed.py': 'Superseded by the consolidated fixture suite.'
        }
    }
    (tmp_path / '.test-deletions.json').write_text(
        json.dumps(policy), encoding='utf-8'
    )
    run_git(tmp_path, 'add', '--', '.test-deletions.json')
    approved = run_gate(TEST_INTEGRITY, tmp_path)

    assert approved.returncode == 0


def test_lockfile_sync_requires_uv_lock_for_a_pyproject_change(
    tmp_path: Path,
) -> None:
    """An unrelated requirements file cannot satisfy this uv project's lock gate."""
    initialize_git_repository(tmp_path)
    (tmp_path / 'pyproject.toml').write_text(
        '[project]\nname = "quality-test"\nversion = "0.1.0"\n',
        encoding='utf-8',
    )
    (tmp_path / 'requirements.txt').write_text('pytest\n', encoding='utf-8')
    run_git(tmp_path, 'add', '--', 'pyproject.toml', 'requirements.txt')

    result = run_gate(LOCKFILE_SYNC, tmp_path)

    assert result.returncode == 1
    assert 'uv.lock' in result.stderr


def test_lockfile_sync_skips_unrelated_staged_changes(tmp_path: Path) -> None:
    """The lock gate must not inspect unrelated staged documentation changes."""
    initialize_git_repository(tmp_path)
    (tmp_path / 'README.md').write_text('Documentation.\n', encoding='utf-8')
    run_git(tmp_path, 'add', '--', 'README.md')

    result = run_gate(LOCKFILE_SYNC, tmp_path)

    assert result.returncode == 0
    assert 'SKIP' in result.stdout


def test_shell_syntax_rejects_then_accepts_staged_shell_script(
    tmp_path: Path,
) -> None:
    """The shell gate must fail on invalid Bash and pass after the fix."""
    initialize_git_repository(tmp_path)
    shell_file = tmp_path / 'scripts' / 'broken.sh'
    shell_file.parent.mkdir()
    shell_file.write_text(
        '#!/usr/bin/env bash\nif true; then\n  echo "missing fi"\n',
        encoding='utf-8',
    )
    run_git(tmp_path, 'add', '--', 'scripts/broken.sh')

    failed = run_gate(SHELL_SYNTAX, tmp_path)

    assert failed.returncode == 1
    assert '[SHELL_SYNTAX]' in failed.stderr
    assert 'broken.sh' in failed.stderr

    shell_file.write_text(
        '#!/usr/bin/env bash\nif true; then\n  echo "valid"\nfi\n',
        encoding='utf-8',
    )
    run_git(tmp_path, 'add', '--', 'scripts/broken.sh')

    passed = run_gate(SHELL_SYNTAX, tmp_path)

    assert passed.returncode == 0


def test_shell_syntax_rejects_an_extensionless_bash_script(
    tmp_path: Path,
) -> None:
    """A shell shebang must be enough to include an extensionless script."""
    initialize_git_repository(tmp_path)
    shell_file = tmp_path / 'scripts' / 'check'
    shell_file.parent.mkdir()
    shell_file.write_text(
        '#!/usr/bin/env bash\nif true; then\n  echo "missing fi"\n',
        encoding='utf-8',
    )
    run_git(tmp_path, 'add', '--', 'scripts/check')

    result = run_gate(SHELL_SYNTAX, tmp_path)

    assert result.returncode == 1
    assert '[SHELL_SYNTAX]' in result.stderr


def test_shell_syntax_uses_staged_content_not_the_worktree(
    tmp_path: Path,
) -> None:
    """An unstaged edit cannot alter the shell syntax result for a commit."""
    initialize_git_repository(tmp_path)
    shell_file = tmp_path / 'scripts' / 'check.sh'
    shell_file.parent.mkdir()
    shell_file.write_text(
        '#!/usr/bin/env bash\necho "valid"\n', encoding='utf-8'
    )
    run_git(tmp_path, 'add', '--', 'scripts/check.sh')

    shell_file.write_text(
        '#!/usr/bin/env bash\nif true; then\n  echo "missing fi"\n',
        encoding='utf-8',
    )
    result = run_gate(SHELL_SYNTAX, tmp_path)

    assert result.returncode == 0


def test_shell_syntax_scans_an_explicit_commit_range(tmp_path: Path) -> None:
    """The CI range mode must validate committed shell content, not the index."""
    initialize_git_repository(tmp_path)
    shell_file = tmp_path / 'scripts' / 'check.sh'
    shell_file.parent.mkdir()
    shell_file.write_text(
        '#!/usr/bin/env bash\necho "valid"\n', encoding='utf-8'
    )
    run_git(tmp_path, 'add', '--', 'scripts/check.sh')
    run_git(tmp_path, 'commit', '--quiet', '-m', 'baseline')

    shell_file.write_text(
        '#!/usr/bin/env bash\nif true; then\n  echo "missing fi"\n',
        encoding='utf-8',
    )
    run_git(tmp_path, 'add', '--', 'scripts/check.sh')
    run_git(tmp_path, 'commit', '--quiet', '-m', 'break shell syntax')

    result = run_gate(SHELL_SYNTAX, tmp_path, '--range', 'HEAD~1...HEAD')

    assert result.returncode == 1
    assert '[SHELL_SYNTAX]' in result.stderr


@pytest.mark.parametrize('script', [DIFF_SANITY, TEST_INTEGRITY, SHELL_SYNTAX])
def test_gates_skip_when_no_relevant_staged_change(
    tmp_path: Path, script: Path
) -> None:
    """Each staged-file gate must be safe and explicit when there is no work."""
    initialize_git_repository(tmp_path)
    (tmp_path / 'README.md').write_text(
        'No relevant change.\n', encoding='utf-8'
    )
    run_git(tmp_path, 'add', '--', 'README.md')

    result = run_gate(script, tmp_path)

    assert result.returncode == 0
