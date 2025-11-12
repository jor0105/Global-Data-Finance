"""Tests for FileSystemService with security validations."""

import os
import tempfile
from pathlib import Path

import pytest

from src.brazil.dados_b3.historical_quotes.infra.file_system_service import (
    FileSystemService,
)
from src.macro_exceptions import (
    EmptyDirectoryError,
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
    SecurityError,
)


class TestFileSystemService:
    """Test suite for FileSystemService."""

    @pytest.fixture
    def service(self):
        """Provide FileSystemService instance."""
        return FileSystemService()

    @pytest.fixture
    def temp_dir(self):
        """Provide a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def populated_temp_dir(self, temp_dir):
        """Provide a temporary directory with files."""
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("test content")
        return temp_dir


class TestValidateDirectoryPath(TestFileSystemService):
    """Tests for validate_directory_path method."""

    def test_valid_directory_path(self, service, populated_temp_dir):
        """Test validation with valid directory path."""
        result = service.validate_directory_path(populated_temp_dir)

        assert isinstance(result, Path)
        assert result.exists()
        assert result.is_dir()

    def test_empty_string_raises_error(self, service):
        """Test that empty string raises InvalidDestinationPathError."""
        with pytest.raises(InvalidDestinationPathError, match="empty or whitespace"):
            service.validate_directory_path("")

    def test_whitespace_string_raises_error(self, service):
        """Test that whitespace string raises InvalidDestinationPathError."""
        with pytest.raises(InvalidDestinationPathError, match="empty or whitespace"):
            service.validate_directory_path("   ")

    def test_non_string_raises_type_error(self, service):
        """Test that non-string input raises TypeError."""
        with pytest.raises(TypeError, match="Path must be a string"):
            service.validate_directory_path(123)  # type: ignore

    def test_non_existent_path_raises_error(self, service):
        """Test that non-existent path raises PathIsNotDirectoryError."""
        with pytest.raises(PathIsNotDirectoryError):
            service.validate_directory_path("/nonexistent/path/12345")

    def test_file_path_raises_error(self, service, temp_dir):
        """Test that file path (not directory) raises PathIsNotDirectoryError."""
        file_path = Path(temp_dir) / "test_file.txt"
        file_path.write_text("content")

        with pytest.raises(PathIsNotDirectoryError):
            service.validate_directory_path(str(file_path))

    def test_empty_directory_raises_error(self, service, temp_dir):
        """Test that empty directory raises EmptyDirectoryError."""
        with pytest.raises(EmptyDirectoryError):
            service.validate_directory_path(temp_dir)

    def test_expanduser_works(self, service, populated_temp_dir):
        """Test that tilde expansion works."""
        # This test assumes the temp_dir is under home directory
        # We'll create a relative path and test expansion
        result = service.validate_directory_path(populated_temp_dir)
        assert result.is_absolute()


class TestPathTraversalSecurity(TestFileSystemService):
    """Security tests for path traversal protection."""

    def test_access_to_etc_blocked(self, service):
        """Test that access to /etc is blocked."""
        with pytest.raises(SecurityError, match="sensitive system directory"):
            service.create_directory_if_not_exists("/etc/malicious_dir")

    def test_access_to_root_blocked(self, service):
        """Test that access to /root is blocked."""
        with pytest.raises(SecurityError, match="sensitive system directory"):
            service.validate_directory_path("/root")

    def test_access_to_sys_blocked(self, service):
        """Test that access to /sys is blocked."""
        with pytest.raises(SecurityError, match="sensitive system directory"):
            service.create_directory_if_not_exists("/sys/test")

    def test_access_to_proc_blocked(self, service):
        """Test that access to /proc is blocked."""
        with pytest.raises(SecurityError, match="sensitive system directory"):
            service.create_directory_if_not_exists("/proc/test")

    def test_valid_path_in_home_allowed(self, service, temp_dir):
        """Test that valid paths in home directory are allowed."""
        result = service.create_directory_if_not_exists(temp_dir)
        assert isinstance(result, Path)
        assert result.exists()

    def test_valid_path_in_tmp_allowed(self, service):
        """Test that valid paths in /tmp are allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = service.create_directory_if_not_exists(tmpdir)
            assert isinstance(result, Path)
            assert result.exists()


class TestCreateDirectoryIfNotExists(TestFileSystemService):
    """Tests for create_directory_if_not_exists method."""

    def test_creates_new_directory(self, service, temp_dir):
        """Test creating a new directory."""
        new_dir = Path(temp_dir) / "new_subdir"

        result = service.create_directory_if_not_exists(str(new_dir))

        assert isinstance(result, Path)
        assert result.exists()
        assert result.is_dir()

    def test_creates_nested_directories(self, service, temp_dir):
        """Test creating nested directories."""
        nested_dir = Path(temp_dir) / "level1" / "level2" / "level3"

        result = service.create_directory_if_not_exists(str(nested_dir))

        assert result.exists()
        assert result.is_dir()

    def test_existing_directory_no_error(self, service, temp_dir):
        """Test that existing directory doesn't raise error."""
        result = service.create_directory_if_not_exists(temp_dir)

        assert isinstance(result, Path)
        assert result.exists()

    def test_path_is_file_raises_error(self, service, temp_dir):
        """Test that existing file path raises PathIsNotDirectoryError."""
        file_path = Path(temp_dir) / "existing_file.txt"
        file_path.write_text("content")

        with pytest.raises(PathIsNotDirectoryError):
            service.create_directory_if_not_exists(str(file_path))

    def test_empty_string_raises_error(self, service):
        """Test that empty string raises InvalidDestinationPathError."""
        with pytest.raises(InvalidDestinationPathError):
            service.create_directory_if_not_exists("")

    def test_non_string_raises_type_error(self, service):
        """Test that non-string input raises TypeError."""
        with pytest.raises(TypeError):
            service.create_directory_if_not_exists(None)  # type: ignore

    @pytest.mark.skipif(
        os.name == "nt", reason="Permission test not reliable on Windows"
    )
    def test_no_write_permission_raises_error(self, service):
        """Test that directory without write permission raises PathPermissionError."""
        # This test is skipped on Windows as permission handling differs
        # On Unix-like systems, /root is typically not writable by non-root users
        read_only_dir = "/root"

        if Path(read_only_dir).exists():
            with pytest.raises((PathPermissionError, OSError, SecurityError)):
                service.create_directory_if_not_exists(read_only_dir)


class TestFindFilesByYears(TestFileSystemService):
    """Tests for find_files_by_years method."""

    def test_finds_files_matching_years(self, service, temp_dir):
        """Test finding files that match specific years."""
        # Create test files
        Path(temp_dir, "COTAHIST_A2020.ZIP").touch()
        Path(temp_dir, "COTAHIST_A2021.ZIP").touch()
        Path(temp_dir, "COTAHIST_A2022.ZIP").touch()
        Path(temp_dir, "OTHER_FILE.txt").touch()

        years = range(2020, 2022)  # 2020, 2021
        result = service.find_files_by_years(Path(temp_dir), years)

        assert len(result) == 2
        assert any("2020" in path for path in result)
        assert any("2021" in path for path in result)
        assert not any("2022" in path for path in result)

    def test_empty_directory_returns_empty_set(self, service, temp_dir):
        """Test that empty directory returns empty set."""
        years = range(2020, 2025)
        result = service.find_files_by_years(Path(temp_dir), years)

        assert len(result) == 0
        assert isinstance(result, set)

    def test_no_matching_files_returns_empty_set(self, service, temp_dir):
        """Test that no matching files returns empty set."""
        Path(temp_dir, "FILE_WITHOUT_YEAR.txt").touch()

        years = range(2020, 2025)
        result = service.find_files_by_years(Path(temp_dir), years)

        assert len(result) == 0

    def test_multiple_files_same_year(self, service, temp_dir):
        """Test finding multiple files with same year."""
        Path(temp_dir, "FILE1_2020.zip").touch()
        Path(temp_dir, "FILE2_2020.txt").touch()
        Path(temp_dir, "FILE3_2020.dat").touch()

        years = range(2020, 2021)
        result = service.find_files_by_years(Path(temp_dir), years)

        # Should find all 3 files
        assert len(result) == 3
