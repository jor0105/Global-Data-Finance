"""Canonical and safe member names for ZIP extraction boundaries."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

from ..macro_exceptions import CorruptedZipError

_INVALID_WIN32_CHARS = frozenset('<>:"|?*')
_RESERVED_DOS_NAMES = frozenset({'con', 'prn', 'aux', 'nul'})
_RESERVED_DOS_PREFIXES = frozenset({'com', 'lpt'})


def canonicalize_archive_member_name(
    archive_path: Path, member_name: str
) -> str:
    """Validate a member and return its destination-safe canonical name."""
    if not member_name or '\x00' in member_name:
        _reject(archive_path, 'member name is empty or invalid')

    windows_view = PureWindowsPath(member_name)
    normalized_separators = member_name.replace('\\', '/')
    posix_view = PurePosixPath(normalized_separators)
    if (
        posix_view.is_absolute()
        or windows_view.is_absolute()
        or windows_view.drive
        or '..' in posix_view.parts
    ):
        _reject(archive_path, f'unsafe ZIP member path: {member_name!r}')

    components = [part for part in normalized_separators.split('/') if part]
    if not components:
        _reject(archive_path, f'unsafe ZIP member path: {member_name!r}')
    for component in components:
        _validate_win32_component(archive_path, member_name, component)

    return '/'.join(
        component.rstrip(' .').casefold() for component in components
    )


def _validate_win32_component(
    archive_path: Path, member_name: str, component: str
) -> None:
    """Reject names that are ambiguous or special in the Win32 namespace."""
    if component in {'.', '..'}:
        _reject(archive_path, f'unsafe ZIP member path: {member_name!r}')
    if component.endswith((' ', '.')):
        _reject(
            archive_path,
            f'unsafe Windows ZIP member name: {member_name!r}',
        )
    if any(
        character in _INVALID_WIN32_CHARS or ord(character) < 32
        for character in component
    ):
        _reject(
            archive_path,
            f'unsafe Windows ZIP member name: {member_name!r}',
        )

    canonical = component.rstrip(' .').casefold()
    stem = canonical.split('.', maxsplit=1)[0].rstrip(' .')
    if stem in _RESERVED_DOS_NAMES or _is_numbered_dos_device(stem):
        _reject(
            archive_path,
            f'unsafe Windows ZIP member name: {member_name!r}',
        )


def _is_numbered_dos_device(stem: str) -> bool:
    """Return whether a component is COM1-9 or LPT1-9."""
    if len(stem) != 4 or stem[:3] not in _RESERVED_DOS_PREFIXES:
        return False
    return stem[3] in '123456789'


def _reject(archive_path: Path, reason: str) -> None:
    """Raise the common archive-rejection exception."""
    raise CorruptedZipError(str(archive_path), reason)
