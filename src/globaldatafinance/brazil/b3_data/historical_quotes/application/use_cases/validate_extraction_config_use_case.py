from typing import Tuple

from ...domain import ExtractionConfigServiceB3


class ValidateExtractionConfigUseCaseB3:
    """Use case for validating extraction configuration."""

    @staticmethod
    def execute(processing_mode: str, output_filename: str) -> Tuple[str, str]:
        """Validate processing mode and output filename.

        Args:
            processing_mode: The processing mode to validate.
            output_filename: The output filename to validate.

        Returns:
            Tuple containing validated (processing_mode, output_filename).
        """
        valid_mode = ExtractionConfigServiceB3.validate_processing_mode(
            processing_mode
        )
        valid_filename = ExtractionConfigServiceB3.validate_output_filename(
            output_filename
        )
        return valid_mode, valid_filename
