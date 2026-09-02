"""Regression tests for the shell syntax quality gate."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

import pytest

REPOSITORY_ROOT = Path(__file__).parents[2]
SHELL_SYNTAX = REPOSITORY_ROOT / 'scripts' / 'check-shell-syntax.py'


class ProcessResult(Protocol):
    """Captured result shape returned by the repository process adapter."""

    returncode: int
    stdout: str
    stderr: str


run_process = cast(
    Callable[..., ProcessResult],
    import_module('scripts.process_runner').run_process,
)

pytestmark = pytest.mark.unit


def run_git(repo: Path, *args: str) -> ProcessResult:
    """Run a Git command in an isolated test repository."""
    return run_process(['git', *args], cwd=repo)


def initialize_git_repository(repo: Path) -> None:
    """Initialize a disposable repository with deterministic metadata."""
    run_git(repo, 'init', '--quiet')
    run_git(repo, 'config', 'user.name', 'Quality Gate Tests')
    run_git(repo, 'config', 'user.email', 'quality-gates@example.invalid')


def run_gate(script: Path, repo: Path, *arguments: str) -> ProcessResult:
    """Execute a gate script from an isolated repository."""
    return run_process(
        ['python', str(script), *arguments],
        cwd=repo,
        check=False,
    )


@pytest.fixture
def shell_syntax_module(monkeypatch: pytest.MonkeyPatch):
    """Load the hyphenated shell syntax gate as a test module."""
    monkeypatch.syspath_prepend(str(REPOSITORY_ROOT / 'scripts'))
    spec = importlib.util.spec_from_file_location(
        'check_shell_syntax', SHELL_SYNTAX
    )
    if spec is None or spec.loader is None:
        raise AssertionError('Unable to load check-shell-syntax.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    """Range mode must validate committed shell content, not the index."""
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


def test_shell_syntax_allocation_failure_returns_gate_error(
    shell_syntax_module,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Temporary-file allocation failures must return the gate error status."""
    monkeypatch.setattr(sys, 'argv', ['check-shell-syntax.py'])
    monkeypatch.setattr(
        shell_syntax_module,
        'staged_shell_files',
        lambda _revision_range=None: [
            ('scripts/check.sh', 'echo valid\n', ('sh', '-n'))
        ],
    )

    def fail_allocation(*_args: object, **_kwargs: object) -> object:
        raise OSError('temporary directory unavailable')

    monkeypatch.setattr(
        shell_syntax_module.tempfile,
        'NamedTemporaryFile',
        fail_allocation,
    )

    assert shell_syntax_module.main() == 2
    assert 'ERROR [SHELL_SYNTAX]' in capsys.readouterr().err


def test_shell_syntax_write_failure_is_translated_and_cleaned(
    shell_syntax_module,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A failed Unicode write must not leave a temporary validation file."""
    temporary_path = tmp_path / 'failed-write.sh'

    class FailingTemporaryFile:
        """Context manager that exposes a real path and fails on write."""

        def __init__(self) -> None:
            self.name = str(temporary_path)

        def __enter__(self) -> FailingTemporaryFile:
            temporary_path.touch()
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def write(self, _content: str) -> int:
            raise UnicodeError('cannot encode shell content')

    monkeypatch.setattr(
        shell_syntax_module.tempfile,
        'NamedTemporaryFile',
        lambda **_kwargs: FailingTemporaryFile(),
    )

    with pytest.raises(shell_syntax_module.ShellInspectionError) as caught:
        shell_syntax_module.validate_shell_file(
            'scripts/check.sh', 'echo valid\n', ('sh', '-n')
        )

    assert isinstance(caught.value.__cause__, UnicodeError)
    assert not temporary_path.exists()


def test_shell_syntax_process_runner_failure_preserves_its_cause(
    shell_syntax_module,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A process adapter failure must become a contextual shell error."""
    process_error = shell_syntax_module.ProcessRunnerError('runner failed')
    monkeypatch.setattr(
        shell_syntax_module,
        'run_process',
        lambda *_args, **_kwargs: (_ for _ in ()).throw(process_error),
    )

    with pytest.raises(shell_syntax_module.ShellInspectionError) as caught:
        shell_syntax_module.validate_shell_file(
            'scripts/check.sh', 'echo valid\n', ('sh', '-n')
        )

    assert caught.value.__cause__ is process_error


def test_shell_syntax_cleanup_failure_is_translated(
    shell_syntax_module,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A cleanup failure must also fail closed with its original cause."""
    temporary_path = tmp_path / 'cleanup-failure.sh'

    class TemporaryFile:
        """Context manager used to make cleanup deterministic."""

        def __init__(self) -> None:
            self.name = str(temporary_path)

        def __enter__(self) -> TemporaryFile:
            temporary_path.touch()
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def write(self, content: str) -> int:
            return len(content)

    monkeypatch.setattr(
        shell_syntax_module.tempfile,
        'NamedTemporaryFile',
        lambda **_kwargs: TemporaryFile(),
    )

    def fail_cleanup(_path: Path, *, missing_ok: bool = False) -> None:
        del missing_ok
        raise OSError('cleanup unavailable')

    monkeypatch.setattr(Path, 'unlink', fail_cleanup)

    with pytest.raises(shell_syntax_module.ShellInspectionError) as caught:
        shell_syntax_module.validate_shell_file(
            'scripts/check.sh', 'echo valid\n', ('sh', '-n')
        )

    assert isinstance(caught.value.__cause__, OSError)
