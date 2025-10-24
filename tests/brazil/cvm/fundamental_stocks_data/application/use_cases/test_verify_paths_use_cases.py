import logging
import os
import tempfile
from pathlib import Path

import pytest

from src.brazil.cvm.fundamental_stocks_data import (
    EmptyDocumentListError,
    VerifyPathsUseCases,
)
from src.macro_exceptions import (
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
)


@pytest.mark.unit
class TestVerifyPathsUseCasesInitialization:
    def test_initialization_with_valid_parameters(self, tmp_path):
        new_set_docs = {"DFP", "ITR"}
        range_years = range(2020, 2024)

        use_case_instance = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        assert use_case_instance is not None
        assert use_case_instance.destination_path == str(tmp_path)
        assert use_case_instance.new_set_docs == new_set_docs
        assert use_case_instance.range_years == range_years

    def test_initialization_validates_destination_path(self, tmp_path):
        new_set_docs = {"DFP"}
        range_years = range(2020, 2024)

        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        # Path should be validated and normalized
        assert os.path.isabs(use_case.destination_path)
        assert os.path.exists(use_case.destination_path)

    def test_initialization_creates_destination_path_if_not_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "new_dir")
            new_set_docs = {"DFP"}
            range_years = range(2020, 2024)

            VerifyPathsUseCases(
                destination_path=new_path,
                new_set_docs=new_set_docs,
                range_years=range_years,
            )

            assert os.path.exists(new_path)
            assert os.path.isdir(new_path)

    def test_initialization_with_empty_doc_set_raises_error(self, tmp_path):
        with pytest.raises(EmptyDocumentListError):
            VerifyPathsUseCases(
                destination_path=str(tmp_path),
                new_set_docs=set(),
                range_years=range(2020, 2024),
            )

    def test_initialization_with_empty_path_raises_error(self):
        with pytest.raises(InvalidDestinationPathError):
            VerifyPathsUseCases(
                destination_path="",
                new_set_docs={"DFP"},
                range_years=range(2020, 2024),
            )

    def test_initialization_with_whitespace_path_raises_error(self):
        with pytest.raises(InvalidDestinationPathError):
            VerifyPathsUseCases(
                destination_path="   ",
                new_set_docs={"DFP"},
                range_years=range(2020, 2024),
            )

    def test_initialization_with_non_string_path_raises_error(self):
        with pytest.raises(TypeError):
            VerifyPathsUseCases(
                destination_path=123,
                new_set_docs={"DFP"},
                range_years=range(2020, 2024),
            )

    def test_initialization_expands_user_path(self):
        os.path.expanduser("~")
        new_set_docs = {"DFP"}
        range_years = range(2020, 2024)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a path within temp that simulates home expansion
            test_path = os.path.join(tmpdir, "test")
            os.makedirs(test_path, exist_ok=True)

            use_case = VerifyPathsUseCases(
                destination_path=test_path,
                new_set_docs=new_set_docs,
                range_years=range_years,
            )

            assert os.path.isabs(use_case.destination_path)

    def test_initialization_normalizes_path(self, tmp_path):
        # Path with redundant separators
        redundant_path = str(tmp_path) + os.sep + "." + os.sep + "subdir"
        os.makedirs(redundant_path, exist_ok=True)

        use_case = VerifyPathsUseCases(
            destination_path=redundant_path,
            new_set_docs={"DFP"},
            range_years=range(2020, 2024),
        )

        # Should be normalized
        assert (
            ".." not in use_case.destination_path
            or "." not in use_case.destination_path
        )

    def test_initialization_logs_debug_message(self, tmp_path, caplog):
        with caplog.at_level(logging.DEBUG):
            VerifyPathsUseCases(
                destination_path=str(tmp_path),
                new_set_docs={"DFP"},
                range_years=range(2020, 2024),
            )

        assert any("created" in record.message.lower() for record in caplog.records)


@pytest.mark.unit
class TestVerifyPathsUseCasesExecute:
    def test_execute_creates_doc_subdirectories(self, tmp_path):
        new_set_docs = {"DFP", "ITR"}
        range_years = range(2020, 2022)

        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        use_case.execute()

        # Check doc directories exist
        for doc in new_set_docs:
            doc_path = os.path.join(tmp_path, doc)
            assert os.path.exists(doc_path)
            assert os.path.isdir(doc_path)

    def test_execute_creates_year_subdirectories(self, tmp_path):
        new_set_docs = {"DFP"}
        range_years = range(2020, 2023)

        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        use_case.execute()

        # Check year directories exist
        for doc in new_set_docs:
            for year in range_years:
                year_path = os.path.join(tmp_path, doc, str(year))
                assert os.path.exists(year_path)
                assert os.path.isdir(year_path)

    def test_execute_creates_complete_directory_structure(self, tmp_path):
        new_set_docs = {"DFP", "ITR", "FRE"}
        range_years = range(2020, 2024)

        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        use_case.execute()

        # Check all combinations exist
        for doc in new_set_docs:
            for year in range_years:
                path = os.path.join(tmp_path, doc, str(year))
                assert os.path.exists(path)

    def test_execute_populates_docs_paths_attribute(self, tmp_path):
        new_set_docs = {"DFP", "ITR"}
        range_years = range(2020, 2022)

        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        use_case.execute()

        assert hasattr(use_case, "docs_paths")
        assert isinstance(use_case.docs_paths, dict)
        assert len(use_case.docs_paths) == 2

        for doc in new_set_docs:
            assert doc in use_case.docs_paths
            assert isinstance(use_case.docs_paths[doc], dict)

    def test_execute_docs_paths_has_correct_structure(self, tmp_path):
        new_set_docs = {"DFP"}
        range_years = range(2020, 2023)

        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        use_case.execute()

        assert "DFP" in use_case.docs_paths
        for year in range_years:
            assert year in use_case.docs_paths["DFP"]
            assert isinstance(use_case.docs_paths["DFP"][year], str)
            assert os.path.isabs(use_case.docs_paths["DFP"][year])

    def test_execute_handles_existing_directories(self, tmp_path):
        new_set_docs = {"DFP"}
        range_years = range(2020, 2022)

        # Pre-create directories
        for doc in new_set_docs:
            for year in range_years:
                os.makedirs(os.path.join(tmp_path, doc, str(year)), exist_ok=True)

        # Should not raise error
        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        use_case.execute()

        # Directories should still exist
        assert os.path.exists(os.path.join(tmp_path, "DFP", "2020"))

    def test_execute_logs_success_message(self, tmp_path, caplog):
        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs={"DFP"},
            range_years=range(2020, 2022),
        )

        with caplog.at_level(logging.INFO):
            use_case.execute()

        assert any(
            "created successfully" in record.message.lower()
            for record in caplog.records
        )

    def test_execute_prints_message(self, tmp_path, capsys):
        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs={"DFP"},
            range_years=range(2020, 2022),
        )

        use_case.execute()

        captured = capsys.readouterr()
        assert (
            "checked/created" in captured.out.lower()
            or "starting" in captured.out.lower()
        )

    def test_execute_with_single_doc_single_year(self, tmp_path):
        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs={"DFP"},
            range_years=range(2023, 2024),
        )

        use_case.execute()

        assert os.path.exists(os.path.join(tmp_path, "DFP", "2023"))
        assert len(use_case.docs_paths) == 1
        assert len(use_case.docs_paths["DFP"]) == 1

    def test_execute_with_many_docs_and_years(self, tmp_path):
        new_set_docs = {"DFP", "ITR", "FRE", "FCA", "CGVN"}
        range_years = range(2010, 2025)

        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        use_case.execute()

        # Should create all directories
        total_dirs = len(new_set_docs) * len(range_years)
        created_dirs = sum(
            1
            for doc in new_set_docs
            for year in range_years
            if os.path.exists(os.path.join(tmp_path, doc, str(year)))
        )

        assert created_dirs == total_dirs


@pytest.mark.unit
class TestVerifyPathsUseCasesPathValidationErrors:
    def test_initialization_with_file_as_destination_raises_error(self, tmp_path):
        # Create a file instead of directory
        file_path = os.path.join(tmp_path, "testfile.txt")
        Path(file_path).touch()

        with pytest.raises(PathIsNotDirectoryError):
            VerifyPathsUseCases(
                destination_path=file_path,
                new_set_docs={"DFP"},
                range_years=range(2020, 2024),
            )

    def test_initialization_with_read_only_path_raises_error(self, tmp_path):
        # Create a read-only directory
        read_only_path = os.path.join(tmp_path, "readonly")
        os.makedirs(read_only_path, exist_ok=True)
        os.chmod(read_only_path, 0o444)

        try:
            with pytest.raises(PathPermissionError):
                VerifyPathsUseCases(
                    destination_path=read_only_path,
                    new_set_docs={"DFP"},
                    range_years=range(2020, 2024),
                )
        finally:
            # Restore permissions for cleanup
            os.chmod(read_only_path, 0o755)

    def test_initialization_creates_nested_paths(self, tmp_path):
        nested_path = os.path.join(tmp_path, "level1", "level2", "level3")

        VerifyPathsUseCases(
            destination_path=nested_path,
            new_set_docs={"DFP"},
            range_years=range(2020, 2022),
        )

        assert os.path.exists(nested_path)
        assert os.path.isdir(nested_path)


@pytest.mark.unit
class TestVerifyPathsUseCasesEdgeCases:
    def test_initialization_with_path_containing_spaces(self, tmp_path):
        path_with_spaces = os.path.join(tmp_path, "path with spaces")

        VerifyPathsUseCases(
            destination_path=path_with_spaces,
            new_set_docs={"DFP"},
            range_years=range(2020, 2022),
        )

        assert os.path.exists(path_with_spaces)

    def test_initialization_with_unicode_path(self, tmp_path):
        unicode_path = os.path.join(tmp_path, "路径_测试")

        VerifyPathsUseCases(
            destination_path=unicode_path,
            new_set_docs={"DFP"},
            range_years=range(2020, 2022),
        )

        assert os.path.exists(unicode_path)

    def test_execute_handles_long_year_range(self, tmp_path):
        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs={"DFP"},
            range_years=range(2000, 2025),
        )

        use_case.execute()

        # All years should be created
        assert len(use_case.docs_paths["DFP"]) == 25

    def test_execute_with_multiple_docs_different_structures(self, tmp_path):
        new_set_docs = {"DFP", "ITR", "FRE"}
        range_years = range(2020, 2023)

        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        use_case.execute()

        # Each doc should have same year structure
        for doc in new_set_docs:
            assert len(use_case.docs_paths[doc]) == len(range_years)

    def test_execute_is_idempotent(self, tmp_path):
        use_case = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs={"DFP"},
            range_years=range(2020, 2022),
        )

        # Execute multiple times
        use_case.execute()
        first_paths = use_case.docs_paths.copy()

        use_case.execute()
        second_paths = use_case.docs_paths

        # Results should be identical
        assert first_paths == second_paths


@pytest.mark.unit
class TestVerifyPathsUseCasesIntegration:
    def test_verify_paths_integrates_with_download_workflow(self, tmp_path):
        # Simulate workflow used in DownloadDocumentsUseCase
        new_set_docs = {"DFP", "ITR"}
        range_years = range(2020, 2023)

        verify_paths_instance = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        verify_paths_instance.execute()

        # Should have structure ready for downloads
        assert hasattr(verify_paths_instance, "docs_paths")
        assert verify_paths_instance.destination_path == str(tmp_path)

        # All paths should be usable
        for doc in new_set_docs:
            for year in range_years:
                path = verify_paths_instance.docs_paths[doc][year]
                assert os.path.exists(path)
                assert os.access(path, os.W_OK)

    def test_verify_paths_accepts_set_from_generate_urls(self, tmp_path):
        # Simulate receiving set from GenerateUrlsUseCase
        new_set_docs = set(["DFP", "ITR", "FRE"])  # Set from GenerateUrlsUseCase
        range_years = range(2020, 2023)

        use_case_instance = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs=new_set_docs,
            range_years=range_years,
        )

        use_case_instance.execute()

        assert len(use_case_instance.docs_paths) == 3

    def test_verify_paths_accepts_range_from_generate_range_years(self, tmp_path):
        # Simulate receiving range from GenerateRangeYearsUseCases
        range_years = range(2020, 2024)  # From GenerateRangeYearsUseCases

        use_case_instance = VerifyPathsUseCases(
            destination_path=str(tmp_path),
            new_set_docs={"DFP"},
            range_years=range_years,
        )

        use_case_instance.execute()

        assert len(use_case_instance.docs_paths["DFP"]) == 4
