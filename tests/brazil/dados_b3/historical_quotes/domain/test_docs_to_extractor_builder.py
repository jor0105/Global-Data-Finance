"""Tests for DocsToExtractorBuilder.

Note: The builder now expects already-validated data (Sets, ranges, etc.)
as per Clean Architecture principles. Validation is done in the Application layer.
"""

import pytest

from src.brazil.dados_b3.historical_quotes.domain.builders import DocsToExtractorBuilder
from src.brazil.dados_b3.historical_quotes.domain.entities.docs_to_extractor import (
    DocsToExtractor,
)


class TestDocsToExtractorBuilder:
    """Test suite for DocsToExtractorBuilder.

    These tests focus on the builder's ability to construct entities,
    not on validation logic (which belongs in the Application layer).
    """

    def test_builder_with_all_required_fields(self):
        """Test building with all required fields."""
        builder = DocsToExtractorBuilder()
        result = (
            builder.with_path_of_docs("/path/to/cotahist")
            .with_set_assets({"ações", "etf"})
            .with_range_years(range(2020, 2022))
            .with_destination_path("/path/to/output")
            .with_set_documents_to_download(
                {"COTAHIST_A2020.ZIP", "COTAHIST_A2021.ZIP"}
            )
            .build()
        )

        assert isinstance(result, DocsToExtractor)
        assert result.path_of_docs == "/path/to/cotahist"
        assert result.set_assets == {"ações", "etf"}
        assert result.range_years == range(2020, 2022)
        assert result.destination_path == "/path/to/output"
        assert result.set_documents_to_download == {
            "COTAHIST_A2020.ZIP",
            "COTAHIST_A2021.ZIP",
        }

    def test_builder_with_minimal_fields(self):
        """Test building with minimal required fields."""
        builder = DocsToExtractorBuilder()
        result = (
            builder.with_path_of_docs("/path/to/cotahist")
            .with_set_assets({"ações"})
            .with_range_years(range(2023, 2024))
            .with_destination_path("/path/to/output")
            .build()
        )

        assert isinstance(result, DocsToExtractor)
        assert result.set_documents_to_download == set()  # Default empty set

    def test_builder_missing_path_of_docs(self):
        """Test that building without path_of_docs raises ValueError."""
        builder = DocsToExtractorBuilder()

        with pytest.raises(ValueError) as exc_info:
            (
                builder.with_set_assets({"ações"})
                .with_range_years(range(2023, 2024))
                .with_destination_path("/path")
                .build()
            )

        assert "path_of_docs" in str(exc_info.value)

    def test_builder_missing_assets(self):
        """Test that building without assets raises ValueError."""
        builder = DocsToExtractorBuilder()

        with pytest.raises(ValueError) as exc_info:
            (
                builder.with_path_of_docs("/path/to/cotahist")
                .with_range_years(range(2023, 2024))
                .with_destination_path("/path")
                .build()
            )

        assert "set_assets" in str(exc_info.value)

    def test_builder_missing_year_range(self):
        """Test that building without year range raises ValueError."""
        builder = DocsToExtractorBuilder()

        with pytest.raises(ValueError) as exc_info:
            (
                builder.with_path_of_docs("/path/to/cotahist")
                .with_set_assets({"ações"})
                .with_destination_path("/path")
                .build()
            )

        assert "range_years" in str(exc_info.value)

    def test_builder_missing_destination_path(self):
        """Test that building without destination_path raises ValueError."""
        builder = DocsToExtractorBuilder()

        with pytest.raises(ValueError) as exc_info:
            (
                builder.with_path_of_docs("/path/to/cotahist")
                .with_set_assets({"ações"})
                .with_range_years(range(2023, 2024))
                .build()
            )

        assert "destination_path" in str(exc_info.value)

    def test_builder_fluent_interface(self):
        """Test that all methods return self for chaining."""
        builder = DocsToExtractorBuilder()

        # Verify each method returns the builder instance
        assert builder.with_path_of_docs("/path") is builder
        assert builder.with_set_assets({"ações"}) is builder
        assert builder.with_range_years(range(2023, 2024)) is builder
        assert builder.with_destination_path("/path") is builder
        assert builder.with_set_documents_to_download({"file.zip"}) is builder

    def test_builder_reusability(self):
        """Test that a new builder can be created for each build operation."""
        # First build
        builder1 = DocsToExtractorBuilder()
        result1 = (
            builder1.with_path_of_docs("/path1")
            .with_set_assets({"ações"})
            .with_range_years(range(2023, 2024))
            .with_destination_path("/dest1")
            .build()
        )

        # Second build with different parameters
        builder2 = DocsToExtractorBuilder()
        result2 = (
            builder2.with_path_of_docs("/path2")
            .with_set_assets({"etf"})
            .with_range_years(range(2022, 2023))
            .with_destination_path("/dest2")
            .build()
        )

        # Verify they are different instances with different values
        assert result1 is not result2
        assert result1.set_assets != result2.set_assets
        assert result1.range_years != result2.range_years
        assert result1.path_of_docs != result2.path_of_docs
