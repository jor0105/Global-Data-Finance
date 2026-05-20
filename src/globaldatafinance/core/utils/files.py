"""Filesystem helpers shared across the library."""

from pathlib import Path

from globaldatafinance.core.logging_config import get_logger


def remove_file(filepath: str, log_on_error: bool = True) -> None:
    """Remove a file from disk safely.

    Removes any file from disk, with optional logging on errors. Handles
    missing files gracefully.

    Args:
        filepath: Path to the file to remove.
        log_on_error: If True, logs warnings when file deletion fails.

    Example:
        >>> from globaldatafinance.core.utils.files import remove_file
        >>>
        >>> remove_file("/path/to/file.zip")
    """
    logger = get_logger(__name__)
    try:
        path_obj = Path(filepath)
        if path_obj.exists():
            path_obj.unlink()
            logger.debug(f'Removed file: {filepath}')
    except Exception as e:
        if log_on_error:
            logger.warning(f'Failed to remove file {filepath}: {e}')
