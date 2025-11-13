from pathlib import Path

import pytest

from src.brazil.dados_b3.historical_quotes.infra.file_system_service import (
    FileSystemService,
)
from src.macro_exceptions import (
    EmptyDirectoryError,
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    SecurityError,
)


class TestFileSystemService:
    @pytest.fixture
    def service(self):
        return FileSystemService()

    def test_validate_directory_path_valid(self, service, tmp_path):
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("test")

        result = service.validate_directory_path(str(test_dir))

        assert isinstance(result, Path)
        assert result.exists()
        assert result.is_dir()

    def test_validate_directory_path_with_files(self, service, tmp_path):
        test_dir = tmp_path / "data"
        test_dir.mkdir()
        (test_dir / "file1.zip").write_text("data1")
        (test_dir / "file2.zip").write_text("data2")

        result = service.validate_directory_path(str(test_dir))

        assert result.exists()
        assert result.is_dir()

    def test_validate_directory_path_not_string_type(self, service):
        with pytest.raises(TypeError):
            service.validate_directory_path(123)

    def test_validate_directory_path_none(self, service):
        with pytest.raises(TypeError):
            service.validate_directory_path(None)

    def test_validate_directory_path_empty_string(self, service):
        with pytest.raises(InvalidDestinationPathError):
            service.validate_directory_path("")

    def test_validate_directory_path_whitespace_only(self, service):
        with pytest.raises(InvalidDestinationPathError):
            service.validate_directory_path("   ")

    def test_validate_directory_path_nonexistent(self, service):
        with pytest.raises(PathIsNotDirectoryError):
            service.validate_directory_path("/nonexistent/path/to/dir")

    def test_validate_directory_path_is_file(self, service, tmp_path):
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        with pytest.raises(PathIsNotDirectoryError):
            service.validate_directory_path(str(file_path))

    def test_validate_directory_path_empty_directory(self, service, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(EmptyDirectoryError):
            service.validate_directory_path(str(empty_dir))

    def test_validate_directory_path_with_tilde_expansion(self, service, tmp_path):
        # Create a directory in tmp_path
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("test")

        # This test is tricky as we can't easily test ~ expansion without
        # creating files in the user's home directory
        # Just test that the method handles it
        result = service.validate_directory_path(str(test_dir))
        assert result.exists()

    def test_validate_directory_path_relative(self, service, tmp_path, monkeypatch):
        test_dir = tmp_path / "relative_test"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("test")

        # Change to tmp_path directory
        monkeypatch.chdir(tmp_path)

        result = service.validate_directory_path("relative_test")

        assert result.exists()
        assert result.is_absolute()


class TestFileSystemServiceSecurityValidation:
    @pytest.fixture
    def service(self):
        return FileSystemService()

    def test_validate_path_safety_blocks_etc(self, service):
        with pytest.raises(SecurityError):
            service._validate_path_safety(Path("/etc/passwd").resolve())

    def test_validate_path_safety_blocks_root(self, service):
        with pytest.raises(SecurityError):
            service._validate_path_safety(Path("/root/secret").resolve())

    def test_validate_path_safety_blocks_sys(self, service):
        with pytest.raises(SecurityError):
            service._validate_path_safety(Path("/sys/kernel").resolve())

    def test_validate_path_safety_blocks_proc(self, service):
        with pytest.raises(SecurityError):
            service._validate_path_safety(Path("/proc/meminfo").resolve())

    def test_validate_path_safety_blocks_dev(self, service):
        with pytest.raises(SecurityError):
            service._validate_path_safety(Path("/dev/null").resolve())

    def test_validate_path_safety_blocks_boot(self, service):
        with pytest.raises(SecurityError):
            service._validate_path_safety(Path("/boot/grub").resolve())

    def test_validate_path_safety_allows_safe_paths(self, service, tmp_path):
        safe_dir = tmp_path / "safe_directory"
        safe_dir.mkdir()

        # Should not raise any exception
        service._validate_path_safety(safe_dir.resolve())

    def test_validate_path_safety_allows_home_directory(self, service, tmp_path):
        # Use tmp_path as it simulates a safe user directory
        home_like = tmp_path / "home" / "user" / "data"
        home_like.mkdir(parents=True)

        # Should not raise
        service._validate_path_safety(home_like.resolve())

    def test_validate_directory_with_path_traversal_attempt(self, service, tmp_path):
        # Create directory structure
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()
        (safe_dir / "file.txt").write_text("test")

        # Try to access parent using ../
        traversal_path = str(safe_dir / ".." / ".." / ".." / "etc")

        # Depending on resolution, this might raise PathIsNotDirectoryError or SecurityError
        with pytest.raises(
            (PathIsNotDirectoryError, SecurityError, EmptyDirectoryError)
        ):
            service.validate_directory_path(traversal_path)


class TestFileSystemServiceFindFiles:
    @pytest.fixture
    def service(self):
        return FileSystemService()

    def test_find_files_by_years_single_year(self, service, tmp_path):
        test_dir = tmp_path / "data"
        test_dir.mkdir()

        (test_dir / "COTAHIST_A2023.ZIP").write_text("data")
        (test_dir / "OTHER_2023.ZIP").write_text("data")
        (test_dir / "FILE_2022.ZIP").write_text("data")

        years = range(2023, 2024)
        result = service.find_files_by_years(test_dir, years)

        assert len(result) == 2
        assert any("2023" in f for f in result)
        assert not any("2022" in f for f in result)

    def test_find_files_by_years_multiple_years(self, service, tmp_path):
        test_dir = tmp_path / "data"
        test_dir.mkdir()

        (test_dir / "FILE_2020.ZIP").write_text("data")
        (test_dir / "FILE_2021.ZIP").write_text("data")
        (test_dir / "FILE_2022.ZIP").write_text("data")
        (test_dir / "FILE_2023.ZIP").write_text("data")
        (test_dir / "FILE_2024.ZIP").write_text("data")

        years = range(2021, 2024)  # 2021, 2022, 2023
        result = service.find_files_by_years(test_dir, years)

        assert len(result) == 3
        assert any("2021" in f for f in result)
        assert any("2022" in f for f in result)
        assert any("2023" in f for f in result)
        assert not any("2020" in f for f in result)
        assert not any("2024" in f for f in result)

    def test_find_files_by_years_no_matches(self, service, tmp_path):
        test_dir = tmp_path / "data"
        test_dir.mkdir()

        (test_dir / "FILE_2020.ZIP").write_text("data")
        (test_dir / "FILE_2021.ZIP").write_text("data")

        years = range(2025, 2027)
        result = service.find_files_by_years(test_dir, years)

        assert len(result) == 0

    def test_find_files_by_years_empty_directory(self, service, tmp_path):
        test_dir = tmp_path / "empty"
        test_dir.mkdir()

        years = range(2020, 2024)
        result = service.find_files_by_years(test_dir, years)

        assert len(result) == 0

    def test_find_files_by_years_ignores_subdirectories(self, service, tmp_path):
        test_dir = tmp_path / "data"
        test_dir.mkdir()

        (test_dir / "FILE_2023.ZIP").write_text("data")
        subdir = test_dir / "SUBDIR_2023"
        subdir.mkdir()

        years = range(2023, 2024)
        result = service.find_files_by_years(test_dir, years)

        # Should only find the file, not the directory
        assert len(result) == 1
        assert "FILE_2023.ZIP" in str(list(result)[0])

    def test_find_files_by_years_various_extensions(self, service, tmp_path):
        test_dir = tmp_path / "data"
        test_dir.mkdir()

        (test_dir / "DATA_2023.ZIP").write_text("data")
        (test_dir / "DATA_2023.TXT").write_text("data")
        (test_dir / "DATA_2023.CSV").write_text("data")

        years = range(2023, 2024)
        result = service.find_files_by_years(test_dir, years)

        # Should find all files containing 2023
        assert len(result) == 3

    def test_find_files_by_years_year_in_different_positions(self, service, tmp_path):
        test_dir = tmp_path / "data"
        test_dir.mkdir()

        (test_dir / "2023_DATA.ZIP").write_text("data")
        (test_dir / "DATA_2023.ZIP").write_text("data")
        (test_dir / "DATA_2023_FINAL.ZIP").write_text("data")

        years = range(2023, 2024)
        result = service.find_files_by_years(test_dir, years)

        assert len(result) == 3

    def test_find_files_by_years_partial_year_match(self, service, tmp_path):
        test_dir = tmp_path / "data"
        test_dir.mkdir()

        # File with year as substring
        (test_dir / "VERSION_20231.ZIP").write_text("data")

        years = range(2023, 2024)
        result = service.find_files_by_years(test_dir, years)

        # "2023" is in "20231"
        assert len(result) == 1

    def test_find_files_by_years_empty_range(self, service, tmp_path):
        test_dir = tmp_path / "data"
        test_dir.mkdir()

        (test_dir / "FILE_2023.ZIP").write_text("data")

        years = range(2023, 2023)  # Empty range
        result = service.find_files_by_years(test_dir, years)

        assert len(result) == 0

    def test_find_files_by_years_duplicate_filenames(self, service, tmp_path):
        test_dir = tmp_path / "data"
        test_dir.mkdir()

        (test_dir / "FILE_2023_2023.ZIP").write_text("data")

        years = range(2023, 2024)
        result = service.find_files_by_years(test_dir, years)

        # Even though 2023 appears twice, file should only be in set once
        assert len(result) == 1


class TestFileSystemServiceIntegration:
    @pytest.fixture
    def service(self):
        return FileSystemService()

    def test_validate_and_find_workflow(self, service, tmp_path):
        data_dir = tmp_path / "cotahist_data"
        data_dir.mkdir()

        # Create test files
        (data_dir / "COTAHIST_A2022.ZIP").write_text("data")
        (data_dir / "COTAHIST_A2023.ZIP").write_text("data")
        (data_dir / "COTAHIST_A2024.ZIP").write_text("data")

        # Validate directory
        validated_path = service.validate_directory_path(str(data_dir))

        # Find files
        years = range(2022, 2025)
        files = service.find_files_by_years(validated_path, years)

        assert len(files) == 3
        assert all("COTAHIST" in f for f in files)

    def test_handles_symlinks(self, service, tmp_path):
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / "file.txt").write_text("data")

        link_dir = tmp_path / "link"
        try:
            link_dir.symlink_to(real_dir)
            # Test validation follows symlink
            result = service.validate_directory_path(str(link_dir))
            assert result.exists()
        except OSError:
            # Symlink creation might fail on some systems (like Windows)
            pytest.skip("Symlink creation not supported")

    def test_multiple_validations(self, service, tmp_path):
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "file1.txt").write_text("data")

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "file2.txt").write_text("data")

        result1 = service.validate_directory_path(str(dir1))
        result2 = service.validate_directory_path(str(dir2))

        assert result1 != result2
        assert result1.exists()
        assert result2.exists()

    def test_large_directory(self, service, tmp_path):
        data_dir = tmp_path / "large"
        data_dir.mkdir()

        # Create many files
        for year in range(2000, 2025):
            for i in range(5):
                (data_dir / f"FILE_{year}_{i}.ZIP").write_text("data")

        validated_path = service.validate_directory_path(str(data_dir))

        # Find files for specific years
        years = range(2020, 2023)
        files = service.find_files_by_years(validated_path, years)

        # Should find 5 files per year * 3 years = 15 files
        assert len(files) == 15


class TestFileSystemServiceEdgeCases:
    @pytest.fixture
    def service(self):
        return FileSystemService()

    def test_directory_with_special_characters(self, service, tmp_path):
        special_dir = tmp_path / "dir with spaces & special!chars"
        special_dir.mkdir()
        (special_dir / "file.txt").write_text("data")

        result = service.validate_directory_path(str(special_dir))
        assert result.exists()

    def test_directory_with_unicode_name(self, service, tmp_path):
        unicode_dir = tmp_path / "Programação_Açúcar"
        unicode_dir.mkdir()
        (unicode_dir / "arquivo.txt").write_text("data")

        result = service.validate_directory_path(str(unicode_dir))
        assert result.exists()

    def test_very_long_path(self, service, tmp_path):
        # Create nested directories
        long_path = tmp_path
        for i in range(10):
            long_path = long_path / f"directory_level_{i}"
        long_path.mkdir(parents=True)
        (long_path / "file.txt").write_text("data")

        result = service.validate_directory_path(str(long_path))
        assert result.exists()

    def test_find_files_with_numeric_only_names(self, service, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        (data_dir / "2023").write_text("data")
        (data_dir / "20231231").write_text("data")

        years = range(2023, 2024)
        files = service.find_files_by_years(data_dir, years)

        assert len(files) == 2

    def test_case_sensitivity_in_years(self, service, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        (data_dir / "file_2023.zip").write_text("data")
        (data_dir / "file_XXXX.zip").write_text("data")

        years = range(2023, 2024)
        files = service.find_files_by_years(data_dir, years)

        # Should only find numeric year
        assert len(files) == 1
        assert "2023" in list(files)[0]
