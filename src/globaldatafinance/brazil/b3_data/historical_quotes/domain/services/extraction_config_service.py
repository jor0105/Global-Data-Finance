from ...exceptions import InvalidOutputFilename, InvalidProcessingMode
from ..value_objects import ProcessingModeEnumB3


class ExtractionConfigServiceB3:
    """Domain service for validating extraction configuration parameters."""

    @staticmethod
    def validate_processing_mode(mode: str) -> str:
        """Validate the processing mode.

        Args:
            mode: The processing mode string to validate.

        Returns:
            The validated processing mode string (lowercase).

        Raises:
            TypeError: If mode is not a string.
            InvalidProcessingMode: If mode is not a valid processing mode.
        """
        if not isinstance(mode, str):
            raise TypeError(
                f'processing_mode must be a string, got {type(mode).__name__}'
            )

        try:
            # This will raise ValueError if invalid
            valid_mode: str = ProcessingModeEnumB3(mode.lower()).value
            return valid_mode
        except ValueError:
            # Filter to get only the actual mode values (FAST, SLOW), not configuration constants
            valid_modes = [
                m.value for m in ProcessingModeEnumB3 if '_' not in m.name
            ]
            raise InvalidProcessingMode(mode, valid_modes)

    @staticmethod
    def validate_output_filename(filename: str) -> str:
        """Validate the output filename.

        Args:
            filename: The filename to validate.

        Returns:
            The validated filename.

        Raises:
            TypeError: If filename is not a string.
            InvalidOutputFilename: If filename is empty or invalid.
        """
        if not isinstance(filename, str):
            raise TypeError(
                f'output_filename must be a string, got {type(filename).__name__}'
            )

        if not filename.strip():
            raise InvalidOutputFilename(
                'Filename cannot be empty or whitespace'
            )

        if not filename.lower().endswith('.parquet'):
            return f'{filename}.parquet'

        return filename
