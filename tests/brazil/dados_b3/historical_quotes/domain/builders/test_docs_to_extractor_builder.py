"""Tests for DocsToExtractorBuilder."""

import pytest

from src.brazil.dados_b3.historical_quotes.domain.builders import DocsToExtractorBuilder
from src.brazil.dados_b3.historical_quotes.domain.entities import DocsToExtractor


class TestDocsToExtractorBuilder:
    """Test suite for DocsToExtractorBuilder."""

    def test_build_with_all_required_fields(self):
        """Test successful building with all required fields."""
        # Arrange
        builder = DocsToExtractorBuilder()
        path_of_docs = "/path/to/docs"
        set_assets = {"ações", "etf"}
        range_years = range(2020, 2024)
        destination_path = "/path/to/output"
        set_documents = {"COTAHIST_A2020.ZIP", "COTAHIST_A2021.ZIP"}

        # Act
        result = (
            builder.with_path_of_docs(path_of_docs)
            .with_set_assets(set_assets)
            .with_range_years(range_years)
            .with_destination_path(destination_path)
            .with_set_documents_to_download(set_documents)
            .build()
        )

        # Assert
        assert isinstance(result, DocsToExtractor)
        assert result.path_of_docs == path_of_docs
        assert result.set_assets == set_assets
        assert result.range_years == range_years
        assert result.destination_path == destination_path
        assert result.set_documents_to_download == set_documents

    def test_build_without_optional_documents(self):
        """Test building without set_documents_to_download (optional field)."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act
        result = (
            builder.with_path_of_docs("/path/to/docs")
            .with_set_assets({"ações"})
            .with_range_years(range(2020, 2024))
            .with_destination_path("/path/to/output")
            .build()
        )

        # Assert
        assert isinstance(result, DocsToExtractor)
        assert result.set_documents_to_download == set()

    def test_build_fails_without_path_of_docs(self):
        """Test that build fails when path_of_docs is missing."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            (
                builder.with_set_assets({"ações"})
                .with_range_years(range(2020, 2024))
                .with_destination_path("/path/to/output")
                .build()
            )

        assert "path_of_docs" in str(exc_info.value)
        assert "Missing required fields" in str(exc_info.value)

    def test_build_fails_without_set_assets(self):
        """Test that build fails when set_assets is missing."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            (
                builder.with_path_of_docs("/path/to/docs")
                .with_range_years(range(2020, 2024))
                .with_destination_path("/path/to/output")
                .build()
            )

        assert "set_assets" in str(exc_info.value)
        assert "Missing required fields" in str(exc_info.value)

    def test_build_fails_without_range_years(self):
        """Test that build fails when range_years is missing."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            (
                builder.with_path_of_docs("/path/to/docs")
                .with_set_assets({"ações"})
                .with_destination_path("/path/to/output")
                .build()
            )

        assert "range_years" in str(exc_info.value)
        assert "Missing required fields" in str(exc_info.value)

    def test_build_fails_without_destination_path(self):
        """Test that build fails when destination_path is missing."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            (
                builder.with_path_of_docs("/path/to/docs")
                .with_set_assets({"ações"})
                .with_range_years(range(2020, 2024))
                .build()
            )

        assert "destination_path" in str(exc_info.value)
        assert "Missing required fields" in str(exc_info.value)

    def test_build_fails_with_multiple_missing_fields(self):
        """Test that build fails and lists all missing fields."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            builder.build()

        error_message = str(exc_info.value)
        assert "Missing required fields" in error_message
        assert "path_of_docs" in error_message
        assert "set_assets" in error_message
        assert "range_years" in error_message
        assert "destination_path" in error_message

    def test_builder_method_chaining(self):
        """Test that builder methods return self for chaining."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act
        result1 = builder.with_path_of_docs("/path")
        result2 = result1.with_set_assets({"ações"})
        result3 = result2.with_range_years(range(2020, 2021))
        result4 = result3.with_destination_path("/output")
        result5 = result4.with_set_documents_to_download({"doc.ZIP"})

        # Assert
        assert result1 is builder
        assert result2 is builder
        assert result3 is builder
        assert result4 is builder
        assert result5 is builder

    def test_builder_can_be_reused(self):
        """Test that a new builder can be created for each entity."""
        # Arrange
        builder1 = DocsToExtractorBuilder()
        entity1 = (
            builder1.with_path_of_docs("/path1")
            .with_set_assets({"ações"})
            .with_range_years(range(2020, 2021))
            .with_destination_path("/output1")
            .build()
        )

        builder2 = DocsToExtractorBuilder()
        entity2 = (
            builder2.with_path_of_docs("/path2")
            .with_set_assets({"etf"})
            .with_range_years(range(2021, 2022))
            .with_destination_path("/output2")
            .build()
        )

        # Assert
        assert entity1.path_of_docs == "/path1"
        assert entity2.path_of_docs == "/path2"
        assert entity1 != entity2

    def test_builder_with_empty_sets(self):
        """Test builder with empty sets for assets and documents."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act
        result = (
            builder.with_path_of_docs("/path/to/docs")
            .with_set_assets(set())
            .with_range_years(range(2020, 2024))
            .with_destination_path("/path/to/output")
            .with_set_documents_to_download(set())
            .build()
        )

        # Assert
        assert result.set_assets == set()
        assert result.set_documents_to_download == set()

    def test_builder_with_empty_range(self):
        """Test builder with empty year range."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act
        result = (
            builder.with_path_of_docs("/path/to/docs")
            .with_set_assets({"ações"})
            .with_range_years(range(2020, 2020))
            .with_destination_path("/path/to/output")
            .build()
        )

        # Assert
        assert list(result.range_years) == []

    def test_builder_with_single_year_range(self):
        """Test builder with single year in range."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act
        result = (
            builder.with_path_of_docs("/path/to/docs")
            .with_set_assets({"ações"})
            .with_range_years(range(2020, 2021))
            .with_destination_path("/path/to/output")
            .build()
        )

        # Assert
        assert list(result.range_years) == [2020]

    def test_builder_with_long_year_range(self):
        """Test builder with long year range."""
        # Arrange
        builder = DocsToExtractorBuilder()
        year_range = range(1986, 2025)

        # Act
        result = (
            builder.with_path_of_docs("/path/to/docs")
            .with_set_assets({"ações"})
            .with_range_years(year_range)
            .with_destination_path("/path/to/output")
            .build()
        )

        # Assert
        assert result.range_years == year_range
        assert len(list(result.range_years)) == 39

    def test_builder_with_all_asset_classes(self):
        """Test builder with all available asset classes."""
        # Arrange
        builder = DocsToExtractorBuilder()
        all_assets = {
            "ações",
            "etf",
            "opções",
            "termo",
            "exercicio_opcoes",
            "forward",
            "leilao",
        }

        # Act
        result = (
            builder.with_path_of_docs("/path/to/docs")
            .with_set_assets(all_assets)
            .with_range_years(range(2020, 2024))
            .with_destination_path("/path/to/output")
            .build()
        )

        # Assert
        assert result.set_assets == all_assets

    def test_builder_with_special_characters_in_paths(self):
        """Test builder with special characters in paths."""
        # Arrange
        builder = DocsToExtractorBuilder()
        path_with_special = "/path/with spaces/and-dashes_underscores"
        dest_with_special = "/output/path/with.dots/and@symbols"

        # Act
        result = (
            builder.with_path_of_docs(path_with_special)
            .with_set_assets({"ações"})
            .with_range_years(range(2020, 2024))
            .with_destination_path(dest_with_special)
            .build()
        )

        # Assert
        assert result.path_of_docs == path_with_special
        assert result.destination_path == dest_with_special

    def test_builder_with_large_document_set(self):
        """Test builder with large set of documents."""
        # Arrange
        builder = DocsToExtractorBuilder()
        large_doc_set = {f"COTAHIST_A{year}.ZIP" for year in range(1986, 2025)}

        # Act
        result = (
            builder.with_path_of_docs("/path/to/docs")
            .with_set_assets({"ações"})
            .with_range_years(range(1986, 2025))
            .with_destination_path("/path/to/output")
            .with_set_documents_to_download(large_doc_set)
            .build()
        )

        # Assert
        assert len(result.set_documents_to_download) == 39

    def test_builder_overwrite_values(self):
        """Test that builder allows overwriting values before build."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act
        result = (
            builder.with_path_of_docs("/first/path")
            .with_path_of_docs("/second/path")
            .with_set_assets({"ações"})
            .with_set_assets({"etf"})
            .with_range_years(range(2020, 2021))
            .with_range_years(range(2021, 2022))
            .with_destination_path("/first/output")
            .with_destination_path("/second/output")
            .build()
        )

        # Assert - should use the last set values
        assert result.path_of_docs == "/second/path"
        assert result.set_assets == {"etf"}
        assert result.range_years == range(2021, 2022)
        assert result.destination_path == "/second/output"

    def test_builder_initialization_state(self):
        """Test that builder initializes with correct default state."""
        # Arrange & Act
        builder = DocsToExtractorBuilder()

        # Assert - internal state should be None for required fields
        assert builder._path_of_docs is None
        assert builder._set_assets is None
        assert builder._range_years is None
        assert builder._destination_path is None
        assert builder._set_documents_to_download == set()

    def test_builder_error_message_clarity(self):
        """Test that error messages are clear and helpful."""
        # Arrange
        builder = DocsToExtractorBuilder()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            builder.with_path_of_docs("/path").build()

        error_message = str(exc_info.value)
        assert "Missing required fields" in error_message
        assert "with_" in error_message
        assert "before calling build()" in error_message
