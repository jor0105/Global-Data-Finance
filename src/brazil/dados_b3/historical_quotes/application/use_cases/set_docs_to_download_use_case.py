from typing import Set

from ...domain.value_objects.validate_paths import ValidatePaths


class CreateSetToDownloadUseCase:
    @staticmethod
    def execute(range_years: range, path: str) -> Set[str]:
        document_set = ValidatePaths().create_set_document_to_download(
            range_years, path
        )
        return document_set
