"""Tests for DownloadPathDTO."""

import os
import tempfile

import pytest

from src.brasil.dados_cvm.dados_fundamentalistas_ações.application.dtos import (
    DownloadPathDTO,
)


class TestDownloadPathDTOValidation:
    """Test DownloadPathDTO input validation and directory creation."""

    def test_valid_dto_with_existing_directory(self):
        """Test creating DTO with valid existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dto = DownloadPathDTO(
                destination_path=tmpdir,
                doc_types=["DFP", "ITR"],
                start_year=2020,
                end_year=2023,
            )

            assert dto.destination_path == os.path.abspath(tmpdir)
            assert dto.doc_types == ["DFP", "ITR"]
            assert dto.start_year == 2020
            assert dto.end_year == 2023

    def test_dto_creates_nonexistent_directory(self):
        """Test that DTO creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "downloads")

            # Verify directory doesn't exist yet
            assert not os.path.exists(new_path)

            dto = DownloadPathDTO(
                destination_path=new_path,
                doc_types=["DFP"],
                start_year=2020,
                end_year=2023,
            )

            # Verify directory was created
            assert os.path.exists(new_path)
            assert os.path.isdir(new_path)
            assert dto.destination_path == os.path.abspath(new_path)

    def test_dto_creates_nested_directories(self):
        """Test that DTO creates nested directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "a", "b", "c", "downloads")

            # Verify nested directories don't exist
            assert not os.path.exists(nested_path)

            DownloadPathDTO(destination_path=nested_path)

            # Verify all nested directories were created
            assert os.path.exists(nested_path)
            assert os.path.isdir(nested_path)

    def test_invalid_path_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty or whitespace"):
            DownloadPathDTO(destination_path="")

    def test_invalid_path_whitespace(self):
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty or whitespace"):
            DownloadPathDTO(destination_path="   ")

    def test_invalid_path_not_string(self):
        """Test that non-string path raises TypeError."""
        with pytest.raises(TypeError, match="must be a string"):
            DownloadPathDTO(destination_path=123)

    def test_invalid_path_file_instead_of_directory(self):
        """Test that file path instead of directory raises ValueError."""
        with tempfile.NamedTemporaryFile() as tmpfile:
            with pytest.raises(ValueError, match="must be a directory"):
                DownloadPathDTO(destination_path=tmpfile.name)

    def test_invalid_path_readonly_parent_directory(self):
        """Test that read-only parent directory raises OSError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a subdirectory
            readonly_dir = os.path.join(tmpdir, "readonly")
            os.makedirs(readonly_dir)

            # Make it read-only
            os.chmod(readonly_dir, 0o444)

            try:
                target_path = os.path.join(readonly_dir, "downloads")

                with pytest.raises(OSError, match="Permission denied|Failed to create"):
                    DownloadPathDTO(destination_path=target_path)
            finally:
                # Restore permissions for cleanup
                os.chmod(readonly_dir, 0o755)

    def test_dto_with_optional_parameters(self):
        """Test DTO with None optional parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dto = DownloadPathDTO(destination_path=tmpdir)

            assert dto.destination_path == os.path.abspath(tmpdir)
            assert dto.doc_types is None
            assert dto.start_year is None
            assert dto.end_year is None

    def test_dto_string_representation(self):
        """Test DTO __repr__ method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dto = DownloadPathDTO(
                destination_path=tmpdir,
                doc_types=["DFP"],
                start_year=2020,
                end_year=2023,
            )

            repr_str = repr(dto)
            assert "DownloadPathDTO" in repr_str
            assert "destination_path" in repr_str
            assert "doc_types" in repr_str

    def test_path_normalization(self):
        """Test that paths are normalized to absolute paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create relative path
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                dto = DownloadPathDTO(destination_path=".")

                assert os.path.isabs(dto.destination_path)
                assert dto.destination_path == os.path.abspath(".")
            finally:
                os.chdir(original_cwd)

    def test_dto_with_all_parameters(self):
        """Test DTO creation with all parameters specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dto = DownloadPathDTO(
                destination_path=tmpdir,
                doc_types=["DFP", "ITR", "FRE"],
                start_year=2015,
                end_year=2024,
            )

            assert dto.destination_path == os.path.abspath(tmpdir)
            assert dto.doc_types == ["DFP", "ITR", "FRE"]
            assert dto.start_year == 2015
            assert dto.end_year == 2024


class TestDownloadPathDTOPathValidationDetails:
    """Test specific path validation scenarios."""

    def test_path_with_tilde_expansion(self):
        """Test that tilde in path is expanded correctly."""
        home_path = os.path.expanduser("~")

        # Create temp directory in home
        with tempfile.TemporaryDirectory(dir=home_path) as tmpdir:
            tilde_path = "~/" + os.path.basename(tmpdir)

            dto = DownloadPathDTO(destination_path=tilde_path)

            # Should be normalized to absolute path
            assert os.path.isabs(dto.destination_path)
            assert "~" not in dto.destination_path

    def test_path_with_relative_components(self):
        """Test that paths with .. are normalized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)

            # Create path with .. component
            path_with_dots = os.path.join(subdir, "..", "downloads")

            dto = DownloadPathDTO(destination_path=path_with_dots)

            # Directory should be created and path normalized
            assert os.path.exists(dto.destination_path)
            assert ".." not in dto.destination_path
            assert os.path.isabs(dto.destination_path)

    def test_write_permission_check_on_existing_directory(self):
        """Test that write permissions are checked on existing directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a writable subdirectory
            writable_dir = os.path.join(tmpdir, "writable")
            os.makedirs(writable_dir)

            # Should succeed
            dto = DownloadPathDTO(destination_path=writable_dir)
            assert os.path.isabs(dto.destination_path)

    def test_dto_idempotent_when_directory_exists(self):
        """Test that creating DTO multiple times with same path is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "downloads")

            # First creation - should create directory
            dto1 = DownloadPathDTO(destination_path=new_path)
            assert os.path.exists(new_path)

            # Second creation - should work fine
            dto2 = DownloadPathDTO(destination_path=new_path)
            assert dto1.destination_path == dto2.destination_path
            assert os.path.exists(new_path)
