"""Comprehensive tests for ValidateDownloadRequestUseCase.

This module tests all possible scenarios for the validation use case,
including success cases and all types of errors.
"""

import os
import tempfile

import pytest

from src.brazil.cvm.fundamental_stocks_data.application.dtos import DownloadPathDTO
from src.brazil.cvm.fundamental_stocks_data.application.use_cases import (
    ValidateDownloadRequestUseCase,
)
from src.brazil.cvm.fundamental_stocks_data.exceptions import (
    EmptyDocumentListError,
    InvalidDestinationPathError,
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    PathIsNotDirectoryError,
    PathPermissionError,
)


class TestValidateDownloadRequestUseCaseSuccess:
    """Test successful validation scenarios."""

    def test_validate_with_all_parameters(self, tmp_path):
        """Test validation with all parameters provided."""
        validator = ValidateDownloadRequestUseCase()

        result = validator.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP", "ITR"],
            start_year=2020,
            end_year=2023,
        )

        assert isinstance(result, DownloadPathDTO)
        assert result.destination_path == str(tmp_path)
        assert result.doc_types == ["DFP", "ITR"]
        assert result.start_year == 2020
        assert result.end_year == 2023

    def test_validate_with_none_doc_types_uses_all(self, tmp_path):
        """Test that None doc_types defaults to all available documents."""
        validator = ValidateDownloadRequestUseCase()

        result = validator.execute(
            destination_path=str(tmp_path),
            doc_types=None,
            start_year=2020,
            end_year=2023,
        )

        assert isinstance(result.doc_types, list)
        assert len(result.doc_types) > 0
        # Should include common doc types
        assert "DFP" in result.doc_types
        assert "ITR" in result.doc_types

    def test_validate_with_none_years_uses_defaults(self, tmp_path):
        """Test that None years default to available range."""
        validator = ValidateDownloadRequestUseCase()

        result = validator.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=None,
            end_year=None,
        )

        assert isinstance(result.start_year, int)
        assert isinstance(result.end_year, int)
        assert result.start_year >= 2010  # Min year
        assert result.end_year >= result.start_year

    def test_validate_creates_directory_if_not_exists(self):
        """Test that validation creates the directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "new_directory", "nested")

            validator = ValidateDownloadRequestUseCase()
            result = validator.execute(
                destination_path=new_path,
                doc_types=["DFP"],
                start_year=2020,
                end_year=2020,
            )

            assert os.path.exists(result.destination_path)
            assert os.path.isdir(result.destination_path)

    def test_validate_with_existing_directory(self, tmp_path):
        """Test validation with an already existing directory."""
        validator = ValidateDownloadRequestUseCase()

        result = validator.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=2020,
            end_year=2020,
        )

        assert result.destination_path == str(tmp_path)

    def test_validate_with_single_doc_type(self, tmp_path):
        """Test validation with a single document type."""
        validator = ValidateDownloadRequestUseCase()

        result = validator.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=2020,
            end_year=2020,
        )

        assert result.doc_types == ["DFP"]

    def test_validate_with_single_year(self, tmp_path):
        """Test validation with start_year == end_year."""
        validator = ValidateDownloadRequestUseCase()

        result = validator.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=2023,
            end_year=2023,
        )

        assert result.start_year == 2023
        assert result.end_year == 2023

    def test_validate_with_multiple_doc_types(self, tmp_path):
        """Test validation with multiple document types."""
        validator = ValidateDownloadRequestUseCase()

        doc_types = ["DFP", "ITR", "FRE", "FCA"]
        result = validator.execute(
            destination_path=str(tmp_path),
            doc_types=doc_types,
            start_year=2020,
            end_year=2021,
        )

        assert result.doc_types == doc_types

    def test_validate_normalizes_path(self):
        """Test that path is normalized (expanded and absolute)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use relative path
            os.chdir(tmpdir)
            relative_path = "./downloads"

            validator = ValidateDownloadRequestUseCase()
            result = validator.execute(
                destination_path=relative_path,
                doc_types=["DFP"],
                start_year=2020,
                end_year=2020,
            )

            # Should be absolute
            assert os.path.isabs(result.destination_path)
            assert "downloads" in result.destination_path


class TestValidateDownloadRequestUseCasePathErrors:
    """Test path validation error scenarios."""

    def test_validate_with_empty_path_raises_error(self):
        """Test that empty path raises InvalidDestinationPathError."""
        validator = ValidateDownloadRequestUseCase()

        with pytest.raises(InvalidDestinationPathError, match="cannot be empty"):
            validator.execute(
                destination_path="", doc_types=["DFP"], start_year=2020, end_year=2020
            )

    def test_validate_with_whitespace_path_raises_error(self):
        """Test that whitespace-only path raises InvalidDestinationPathError."""
        validator = ValidateDownloadRequestUseCase()

        with pytest.raises(InvalidDestinationPathError, match="cannot be empty"):
            validator.execute(
                destination_path="   ",
                doc_types=["DFP"],
                start_year=2020,
                end_year=2020,
            )

    def test_validate_with_non_string_path_raises_error(self):
        """Test that non-string path raises InvalidDestinationPathError."""
        validator = ValidateDownloadRequestUseCase()

        with pytest.raises(InvalidDestinationPathError, match="must be a string"):
            validator.execute(
                destination_path=123,  # Not a string
                doc_types=["DFP"],
                start_year=2020,
                end_year=2020,
            )

    def test_validate_with_file_instead_of_directory_raises_error(self, tmp_path):
        """Test that providing a file path instead of directory raises PathIsNotDirectoryError."""
        # Create a file
        file_path = tmp_path / "file.txt"
        file_path.touch()

        validator = ValidateDownloadRequestUseCase()

        with pytest.raises(PathIsNotDirectoryError, match="must be a directory"):
            validator.execute(
                destination_path=str(file_path),
                doc_types=["DFP"],
                start_year=2020,
                end_year=2020,
            )

    def test_validate_with_read_only_directory_raises_error(self, tmp_path):
        """Test that directory without write permission raises PathPermissionError."""
        # Create read-only directory
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o444)  # Read-only

        validator = ValidateDownloadRequestUseCase()

        try:
            with pytest.raises(PathPermissionError, match="No write permission"):
                validator.execute(
                    destination_path=str(read_only_dir),
                    doc_types=["DFP"],
                    start_year=2020,
                    end_year=2020,
                )
        finally:
            # Restore permissions for cleanup
            read_only_dir.chmod(0o755)


class TestValidateDownloadRequestUseCaseDocTypeErrors:
    """Test document type validation error scenarios."""

    def test_validate_with_invalid_doc_type_raises_error(self, tmp_path):
        """Test that invalid document type raises InvalidDocName."""
        validator = ValidateDownloadRequestUseCase()

        with pytest.raises(InvalidDocName):
            validator.execute(
                destination_path=str(tmp_path),
                doc_types=["INVALID_DOC"],
                start_year=2020,
                end_year=2020,
            )

    def test_validate_with_mixed_valid_invalid_docs_raises_error(self, tmp_path):
        """Test that mix of valid and invalid doc types raises error."""
        validator = ValidateDownloadRequestUseCase()

        with pytest.raises(InvalidDocName):
            validator.execute(
                destination_path=str(tmp_path),
                doc_types=["DFP", "INVALID", "ITR"],
                start_year=2020,
                end_year=2020,
            )

    def test_validate_with_empty_doc_list_raises_error(self, tmp_path):
        """Test that empty doc_types list raises EmptyDocumentListError."""
        validator = ValidateDownloadRequestUseCase()

        # Empty list should raise EmptyDocumentListError
        with pytest.raises(EmptyDocumentListError):
            validator.execute(
                destination_path=str(tmp_path),
                doc_types=[],
                start_year=2020,
                end_year=2020,
            )


class TestValidateDownloadRequestUseCaseYearErrors:
    """Test year validation error scenarios."""

    def test_validate_with_start_year_too_old_raises_error(self, tmp_path):
        """Test that start_year before minimum raises InvalidFirstYear."""
        validator = ValidateDownloadRequestUseCase()

        with pytest.raises(InvalidFirstYear):
            validator.execute(
                destination_path=str(tmp_path),
                doc_types=["DFP"],
                start_year=1990,  # Too old
                end_year=2020,
            )

    def test_validate_with_end_year_after_current_raises_error(self, tmp_path):
        """Test that end_year in future raises InvalidLastYear."""
        validator = ValidateDownloadRequestUseCase()

        with pytest.raises(InvalidLastYear):
            validator.execute(
                destination_path=str(tmp_path),
                doc_types=["DFP"],
                start_year=2020,
                end_year=2050,  # In the future
            )

    def test_validate_with_start_greater_than_end_raises_error(self, tmp_path):
        """Test that start_year > end_year raises InvalidLastYear."""
        validator = ValidateDownloadRequestUseCase()

        with pytest.raises(InvalidLastYear):
            validator.execute(
                destination_path=str(tmp_path),
                doc_types=["DFP"],
                start_year=2023,
                end_year=2020,  # end < start
            )

    def test_validate_with_non_integer_year_raises_error(self, tmp_path):
        """Test that non-integer year raises TypeError."""
        validator = ValidateDownloadRequestUseCase()

        with pytest.raises((TypeError, InvalidFirstYear)):
            validator.execute(
                destination_path=str(tmp_path),
                doc_types=["DFP"],
                start_year="2020",  # String instead of int
                end_year=2023,
            )


class TestValidateDownloadRequestUseCaseEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_validate_with_minimum_valid_year(self, tmp_path):
        """Test validation with minimum allowed year (2010)."""
        validator = ValidateDownloadRequestUseCase()

        result = validator.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=2010,
            end_year=2010,
        )

        assert result.start_year == 2010

    def test_validate_with_all_doc_types(self, tmp_path):
        """Test validation with all available document types."""
        validator = ValidateDownloadRequestUseCase()

        all_docs = ["CGVN", "FRE", "FCA", "DFP", "ITR", "IPE", "VLMO"]
        result = validator.execute(
            destination_path=str(tmp_path),
            doc_types=all_docs,
            start_year=2020,
            end_year=2020,
        )

        assert len(result.doc_types) == len(all_docs)

    def test_validate_preserves_doc_type_order(self, tmp_path):
        """Test that document type order is preserved."""
        validator = ValidateDownloadRequestUseCase()

        doc_types = ["ITR", "DFP", "FRE"]  # Non-alphabetical order
        result = validator.execute(
            destination_path=str(tmp_path),
            doc_types=doc_types,
            start_year=2020,
            end_year=2020,
        )

        assert result.doc_types == doc_types

    def test_validate_case_insensitive_doc_types(self, tmp_path):
        """Test that document types are normalized to uppercase."""
        validator = ValidateDownloadRequestUseCase()

        # Should normalize to uppercase
        result = validator.execute(
            destination_path=str(tmp_path),
            doc_types=["dfp", "itr"],  # Lowercase
            start_year=2020,
            end_year=2020,
        )

        # Check that validation passes (case-insensitive)
        assert isinstance(result, DownloadPathDTO)
