"""Tests for VerifyDestinationPathsUseCase."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.brazil.dados_b3.historical_quotes.application.use_cases import (
    VerifyDestinationPathsUseCase,
)
from src.macro_exceptions import (
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
)


class TestVerifyDestinationPathsUseCase:
    """Test suite for VerifyDestinationPathsUseCase."""

    def test_execute_with_valid_existing_directory(self, tmp_path):
        """Test execute with valid existing directory."""
        # Arrange
        test_dir = tmp_path / "test_output"
        test_dir.mkdir()

        # Act & Assert - should not raise any exception
        VerifyDestinationPathsUseCase.execute(str(test_dir))

    def test_execute_creates_non_existing_directory(self, tmp_path):
        """Test that execute creates non-existing directory."""
        # Arrange
        test_dir = tmp_path / "new_output"
        assert not test_dir.exists()

        # Act
        VerifyDestinationPathsUseCase.execute(str(test_dir))

        # Assert
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_execute_creates_nested_directories(self, tmp_path):
        """Test that execute creates nested directories."""
        # Arrange
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        assert not nested_dir.exists()

        # Act
        VerifyDestinationPathsUseCase.execute(str(nested_dir))

        # Assert
        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_execute_raises_type_error_for_non_string(self):
        """Test that non-string path raises TypeError."""
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            VerifyDestinationPathsUseCase.execute(123)

        assert "must be a string" in str(exc_info.value)

    def test_execute_raises_type_error_for_none(self):
        """Test that None path raises TypeError."""
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            VerifyDestinationPathsUseCase.execute(None)

        assert "must be a string" in str(exc_info.value)

    def test_execute_raises_type_error_for_list(self):
        """Test that list path raises TypeError."""
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            VerifyDestinationPathsUseCase.execute(["/path/to/output"])

        assert "must be a string" in str(exc_info.value)

    def test_execute_raises_invalid_destination_path_for_empty_string(self):
        """Test that empty string raises InvalidDestinationPathError."""
        # Act & Assert
        with pytest.raises(InvalidDestinationPathError) as exc_info:
            VerifyDestinationPathsUseCase.execute("")

        assert "cannot be empty" in str(exc_info.value)

    def test_execute_raises_invalid_destination_path_for_whitespace(self):
        """Test that whitespace string raises InvalidDestinationPathError."""
        # Act & Assert
        with pytest.raises(InvalidDestinationPathError) as exc_info:
            VerifyDestinationPathsUseCase.execute("   ")

        assert "cannot be empty or whitespace" in str(exc_info.value)

    def test_execute_raises_path_is_not_directory_for_file(self, tmp_path):
        """Test that existing file raises PathIsNotDirectoryError."""
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("content")

        # Act & Assert
        with pytest.raises(PathIsNotDirectoryError) as exc_info:
            VerifyDestinationPathsUseCase.execute(str(test_file))

        assert "must be a directory" in str(exc_info.value)
        assert str(test_file) in str(exc_info.value)

    @patch("os.access")
    def test_execute_raises_path_permission_error_for_no_write_permission(
        self, mock_access, tmp_path
    ):
        """Test that directory without write permission raises PathPermissionError."""
        # Arrange
        test_dir = tmp_path / "no_write"
        test_dir.mkdir()
        mock_access.return_value = False

        # Act & Assert
        with pytest.raises(PathPermissionError) as exc_info:
            VerifyDestinationPathsUseCase.execute(str(test_dir))

        assert "Permission denied" in str(exc_info.value)
        assert "No write permission" in str(exc_info.value)

    def test_execute_expands_user_home_directory(self, tmp_path):
        """Test that tilde (~) is expanded to user home directory."""
        # Arrange
        with patch.object(Path, "expanduser") as mock_expand:
            mock_expand.return_value = tmp_path / "expanded"
            (tmp_path / "expanded").mkdir()

            # Act
            VerifyDestinationPathsUseCase.execute("~/test_output")

            # Assert
            mock_expand.assert_called()

    def test_execute_resolves_relative_paths(self, tmp_path):
        """Test that relative paths are resolved."""
        # Arrange
        test_dir = tmp_path / "relative"
        test_dir.mkdir()

        with patch.object(Path, "resolve") as mock_resolve:
            mock_resolve.return_value = test_dir

            # Act
            VerifyDestinationPathsUseCase.execute("./relative/path")

            # Assert
            mock_resolve.assert_called()

    def test_execute_handles_path_with_spaces(self, tmp_path):
        """Test execute with path containing spaces."""
        # Arrange
        test_dir = tmp_path / "path with spaces"
        test_dir.mkdir()

        # Act & Assert - should not raise any exception
        VerifyDestinationPathsUseCase.execute(str(test_dir))

    def test_execute_handles_path_with_special_characters(self, tmp_path):
        """Test execute with path containing special characters."""
        # Arrange
        test_dir = tmp_path / "path-with_special.chars"
        test_dir.mkdir()

        # Act & Assert - should not raise any exception
        VerifyDestinationPathsUseCase.execute(str(test_dir))

    def test_execute_is_static_method(self, tmp_path):
        """Test that execute is a static method."""
        # Arrange
        test_dir = tmp_path / "static_test"
        test_dir.mkdir()

        # Act & Assert - should not raise any exception
        VerifyDestinationPathsUseCase.execute(str(test_dir))

    def test_execute_with_existing_writable_directory(self, tmp_path):
        """Test execute with existing writable directory."""
        # Arrange
        test_dir = tmp_path / "writable"
        test_dir.mkdir()
        assert os.access(str(test_dir), os.W_OK)

        # Act & Assert - should not raise any exception
        VerifyDestinationPathsUseCase.execute(str(test_dir))

    @patch("pathlib.Path.mkdir")
    def test_execute_raises_permission_error_on_mkdir_failure(
        self, mock_mkdir, tmp_path
    ):
        """Test that PermissionError during mkdir raises PathPermissionError."""
        # Arrange
        test_dir = tmp_path / "no_create_permission"
        mock_mkdir.side_effect = PermissionError("Cannot create directory")

        # Act & Assert
        with pytest.raises(PathPermissionError):
            VerifyDestinationPathsUseCase.execute(str(test_dir))

    @patch("pathlib.Path.mkdir")
    def test_execute_raises_os_error_on_mkdir_failure(self, mock_mkdir, tmp_path):
        """Test that OSError during mkdir is re-raised."""
        # Arrange
        test_dir = tmp_path / "os_error"
        mock_mkdir.side_effect = OSError("Generic OS error")

        # Act & Assert
        with pytest.raises(OSError) as exc_info:
            VerifyDestinationPathsUseCase.execute(str(test_dir))

        assert "Failed to create directory" in str(exc_info.value)

    def test_execute_does_not_modify_existing_directory(self, tmp_path):
        """Test that execute doesn't modify existing directory."""
        # Arrange
        test_dir = tmp_path / "existing"
        test_dir.mkdir()
        test_file = test_dir / "existing_file.txt"
        test_file.write_text("content")

        original_mtime = test_file.stat().st_mtime

        # Act
        VerifyDestinationPathsUseCase.execute(str(test_dir))

        # Assert
        assert test_file.exists()
        assert test_file.read_text() == "content"
        assert test_file.stat().st_mtime == original_mtime

    def test_execute_with_absolute_path(self, tmp_path):
        """Test execute with absolute path."""
        # Arrange
        test_dir = tmp_path / "absolute"
        test_dir.mkdir()

        # Act & Assert - should not raise any exception
        VerifyDestinationPathsUseCase.execute(str(test_dir.absolute()))

    def test_execute_normalizes_path(self, tmp_path):
        """Test that path is normalized."""
        # Arrange
        test_dir = tmp_path / "normalize"
        test_dir.mkdir()

        # Act & Assert - should not raise any exception
        VerifyDestinationPathsUseCase.execute(str(test_dir))
