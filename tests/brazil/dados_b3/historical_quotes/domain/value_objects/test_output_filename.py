"""Tests for OutputFilename value object."""

import pytest

from src.brazil.dados_b3.historical_quotes.domain.value_objects.output_filename import (
    OutputFilename,
)


class TestOutputFilenameValidation:
    """Tests for OutputFilename validation."""

    def test_simple_filename_is_accepted(self):
        """Test that simple filename is accepted as-is."""
        filename = OutputFilename("my_quotes")
        assert str(filename) == "my_quotes"

    def test_filename_with_underscore_and_dash(self):
        """Test filename with underscore and dash characters."""
        filename = OutputFilename("my-data_2023")
        assert str(filename) == "my-data_2023"

    def test_filename_with_parquet_extension(self):
        """Test that filename with .parquet extension is accepted."""
        filename = OutputFilename("my_quotes.parquet")
        assert str(filename) == "my_quotes.parquet"

    def test_filename_with_numbers(self):
        """Test filename with numbers."""
        filename = OutputFilename("cotahist_2020_2023")
        assert str(filename) == "cotahist_2020_2023"

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            OutputFilename("")

    def test_whitespace_only_raises_error(self):
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            OutputFilename("   ")

    def test_path_with_separator_raises_error(self):
        """Test that path with directory separator raises ValueError."""
        with pytest.raises(ValueError, match="must be a filename, not a path"):
            OutputFilename("/path/to/file")

    def test_path_with_backslash_raises_error(self):
        """Test that path with backslash raises ValueError."""
        with pytest.raises(ValueError, match="invalid characters"):
            OutputFilename("folder\\file")

    def test_filename_with_invalid_characters_raises_error(self):
        """Test that invalid characters raise ValueError."""
        with pytest.raises(ValueError, match="invalid characters"):
            OutputFilename("my@quotes!")

    def test_filename_too_long_raises_error(self):
        """Test that filename exceeding 255 chars raises ValueError."""
        long_name = "a" * 256
        with pytest.raises(ValueError, match="too long"):
            OutputFilename(long_name)

    def test_filename_exactly_255_chars_accepted(self):
        """Test that filename of exactly 255 chars is accepted."""
        name_255_chars = "a" * 255
        filename = OutputFilename(name_255_chars)
        assert str(filename) == name_255_chars

    def test_non_string_type_raises_error(self):
        """Test that non-string type raises ValueError."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            OutputFilename(123)

    def test_none_type_raises_error(self):
        """Test that None type raises ValueError."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            OutputFilename(None)

    def test_filename_value_property_is_immutable(self):
        """Test that OutputFilename value is immutable (frozen dataclass)."""
        filename = OutputFilename("my_quotes")
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            filename.value = "other_quotes"


class TestOutputFilenameExamples:
    """Test real-world examples of OutputFilename usage."""

    def test_example_simple_usage(self):
        """Test simple usage example."""
        filename = OutputFilename("cotahist_extracted")
        assert str(filename) == "cotahist_extracted"

    def test_example_with_year_range(self):
        """Test example with year range in filename."""
        filename = OutputFilename("b3_stocks_2020_2023")
        assert str(filename) == "b3_stocks_2020_2023"

    def test_example_with_asset_type(self):
        """Test example with asset type in filename."""
        filename = OutputFilename("acoes_etf_opcoes")
        assert str(filename) == "acoes_etf_opcoes"

    def test_example_user_provides_extension_explicitly(self):
        """Test that if user provides extension, it's accepted as-is."""
        filename = OutputFilename("my_data.parquet")
        assert str(filename) == "my_data.parquet"


class TestOutputFilenameErrorMessages:
    """Test that error messages are clear and helpful."""

    def test_error_message_for_path(self):
        """Test error message when path is provided."""
        with pytest.raises(ValueError) as exc_info:
            OutputFilename("/data/file")
        assert "not a path" in str(exc_info.value)

    def test_error_message_for_invalid_chars(self):
        """Test error message when invalid characters are used."""
        with pytest.raises(ValueError) as exc_info:
            OutputFilename("file@name!")
        assert "invalid characters" in str(exc_info.value)

    def test_error_message_for_too_long(self):
        """Test error message when filename is too long."""
        with pytest.raises(ValueError) as exc_info:
            OutputFilename("a" * 256)
        assert "too long" in str(exc_info.value)
