from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ExtractorResult:
    """Result of a extraction operation.

    Attributes:
        successful_extractor: List of successfully extracted files/document types.
        failed_extractor: Dictionary mapping document types to error messages.
        success_count_extractor: Number of successful extractions.
        error_count_extractor: Number of failed extractions.
    """

    successful_extractions: List[str] = field(default_factory=list)
    failed_extractions: Dict[str, str] = field(default_factory=dict)

    @property
    def success_count_extractions(self) -> int:
        return len(self.successful_extractions)

    @property
    def error_count_extractions(self) -> int:
        return len(self.failed_extractions)

    def add_success_extractions(self, item: str) -> None:
        if item not in self.successful_extractions:
            self.successful_extractions.append(item)

    def add_error_extractor(self, item: str, error: str) -> None:
        self.failed_extractions[item] = error

    def __str__(self) -> str:
        return (
            f"ExtractorResult(success={self.success_count_extractions}, "
            f"errors={self.error_count_extractions})"
        )
