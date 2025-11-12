from typing import Optional, Set

from ..entities.docs_to_extractor import DocsToExtractor


class DocsToExtractorBuilder:
    """Builder for creating DocsToExtractor entities.

    This builder provides a fluent interface for constructing DocsToExtractor
    entities. It does NOT perform validations or business logic - that should
    be done in the Application layer before calling the builder.

    Following Clean Architecture principles, this Domain layer builder only
    constructs the entity with the provided values.

    Example:
        >>> # In Application layer: validate all data first
        >>> # Then use builder to construct the entity
        >>> builder = DocsToExtractorBuilder()
        >>> docs = (builder
        ...     .with_path_of_docs("/path/to/cotahist")
        ...     .with_set_assets({"ações", "etf"})
        ...     .with_range_years(range(2020, 2024))
        ...     .with_destination_path("/path/to/output")
        ...     .with_set_documents_to_download({"COTAHIST_A2020.ZIP", ...})
        ...     .build())
    """

    def __init__(self):
        """Initialize the builder with default/empty values."""
        self._path_of_docs: Optional[str] = None
        self._set_assets: Optional[Set[str]] = None
        self._range_years: Optional[range] = None
        self._destination_path: Optional[str] = None
        self._set_documents_to_download: Set[str] = set()

    def with_path_of_docs(self, path: str) -> "DocsToExtractorBuilder":
        """Set the path where COTAHIST ZIP files are located.

        Args:
            path: Directory containing COTAHIST ZIP files

        Returns:
            Self for method chaining
        """
        self._path_of_docs = path
        return self

    def with_set_assets(self, set_assets: Set[str]) -> "DocsToExtractorBuilder":
        """Set the set of asset classes to extract.

        Args:
            set_assets: Set of validated asset class codes

        Returns:
            Self for method chaining
        """
        self._set_assets = set_assets
        return self

    def with_range_years(self, range_years: range) -> "DocsToExtractorBuilder":
        """Set the year range for extraction.

        Args:
            range_years: Range object representing the years to process

        Returns:
            Self for method chaining
        """
        self._range_years = range_years
        return self

    def with_destination_path(self, path: str) -> "DocsToExtractorBuilder":
        """Set the destination path for output files.

        Args:
            path: Directory where output files will be saved

        Returns:
            Self for method chaining
        """
        self._destination_path = path
        return self

    def with_set_documents_to_download(
        self, documents: Set[str]
    ) -> "DocsToExtractorBuilder":
        """Set the set of document filenames to download.

        Args:
            documents: Set of document filenames to process

        Returns:
            Self for method chaining
        """
        self._set_documents_to_download = documents
        return self

    def build(self) -> DocsToExtractor:
        """Build the DocsToExtractor entity.

        This method only constructs the entity. All validations should be
        performed in the Application layer before calling this method.

        Returns:
            DocsToExtractor entity

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields (raises ValueError if any are None)
        self._validate_required_fields()

        # After validation, we know these are not None
        # Type checker needs explicit assertion
        assert self._path_of_docs is not None
        assert self._set_assets is not None
        assert self._range_years is not None
        assert self._destination_path is not None

        return DocsToExtractor(
            path_of_docs=self._path_of_docs,
            set_assets=self._set_assets,
            range_years=self._range_years,
            destination_path=self._destination_path,
            set_documents_to_download=self._set_documents_to_download,
        )

    def _validate_required_fields(self) -> None:
        """Validate that all required fields have been set.

        Raises:
            ValueError: If any required field is missing
        """
        missing_fields = []

        if self._path_of_docs is None:
            missing_fields.append("path_of_docs")
        if self._set_assets is None:
            missing_fields.append("set_assets")
        if self._range_years is None:
            missing_fields.append("range_years")
        if self._destination_path is None:
            missing_fields.append("destination_path")

        if missing_fields:
            raise ValueError(
                f"Missing required fields: {', '.join(missing_fields)}. "
                f"Use with_* methods to set all required fields before calling build()."
            )
