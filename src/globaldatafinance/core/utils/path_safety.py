r"""Path-traversal defense shared by the B3 and CVM facade entry points.

Single source of truth for the sensitive-directory blocklist. Both
``FileSystemServiceB3.validate_directory_path`` and
``VerifyPathsUseCasesCVM`` delegate to ``assert_path_not_sensitive`` so a
malicious destination raises :class:`SecurityError` before any ``mkdir``
or write occurs.

Why this exists:
    Before unification, the B3 helper used a path-aware ``relative_to``
    check while the CVM helper used ``str.startswith`` -- which produced
    false positives such as ``/etcd_data`` being blocked because the
    string starts with ``/etc``. Centralising the logic guarantees both
    facades enforce the same blocklist with the same semantics.

Blocklist:
    - POSIX system: /etc, /root, /sys, /proc, /dev, /boot, /usr, /var,
      /lib.
    - User secrets: ~/.ssh, ~/.aws, ~/.gnupg. ``~/.config`` is *not*
      blocked because legitimate per-user config storage uses it.
    - Windows system (cross-platform): C:\Windows, C:\Program Files,
      C:\Program Files (x86). Detected via the raw input string so the
      rule fires even when the running OS is POSIX.
"""

from __future__ import annotations

from pathlib import Path, PureWindowsPath

from ...macro_exceptions import SecurityError

_SENSITIVE_SYSTEM_DIRS: tuple[Path, ...] = (
    Path('/etc'),
    Path('/root'),
    Path('/sys'),
    Path('/proc'),
    Path('/dev'),
    Path('/boot'),
    Path('/usr'),
    Path('/var'),
    Path('/lib'),
)

_USER_SECRET_DIRNAMES: tuple[str, ...] = ('.ssh', '.aws', '.gnupg')

_SENSITIVE_WINDOWS_DIRS: tuple[PureWindowsPath, ...] = (
    PureWindowsPath('C:/Windows'),
    PureWindowsPath('C:/Program Files'),
    PureWindowsPath('C:/Program Files (x86)'),
)


def _has_windows_drive(raw: str) -> bool:
    """True if ``raw`` looks like a Windows drive-letter path."""
    return (
        len(raw) >= 3
        and raw[1] == ':'
        and raw[2] in ('\\', '/')
        and raw[0].isalpha()
    )


def assert_path_not_sensitive(
    path: Path,
    raw_input: str | None = None,
) -> None:
    r"""Raise :class:`SecurityError` if ``path`` lives in a blocked directory.

    Args:
        path: A resolved Path produced by
            ``Path(raw).expanduser().resolve()``. POSIX-system and
            user-secret checks operate on this resolved value, so
            ``../`` traversals cannot escape detection.
        raw_input: Optional original string supplied by the user. When
            provided, enables a Windows drive-letter check that works
            cross-platform: a string such as ``C:\Windows\System32`` is
            rejected even if running on Linux/macOS, where
            ``Path.resolve`` would otherwise mangle the drive.

    Raises:
        SecurityError: If the resolved path or the raw input falls
            inside any sensitive directory listed in the module
            docstring.
    """
    for posix_sensitive in _SENSITIVE_SYSTEM_DIRS:
        try:
            path.relative_to(posix_sensitive)
        except ValueError:
            continue
        raise SecurityError(
            f"Access to sensitive system directory denied: '{path}' "
            f"is within protected path '{posix_sensitive}'",
            path=str(path),
        )

    home = Path.home()
    for secret_name in _USER_SECRET_DIRNAMES:
        secret_dir = home / secret_name
        try:
            path.relative_to(secret_dir)
        except ValueError:
            continue
        raise SecurityError(
            f"Access to sensitive user directory denied: '{path}' "
            f"is within protected path '{secret_dir}'",
            path=str(path),
        )

    candidate_str = raw_input if raw_input is not None else str(path)
    if _has_windows_drive(candidate_str):
        win_path = PureWindowsPath(candidate_str)
        for win_sensitive in _SENSITIVE_WINDOWS_DIRS:
            try:
                win_path.relative_to(win_sensitive)
            except ValueError:
                continue
            raise SecurityError(
                f'Access to sensitive Windows directory denied: '
                f"'{candidate_str}' is within protected path "
                f"'{win_sensitive}'",
                path=candidate_str,
            )
