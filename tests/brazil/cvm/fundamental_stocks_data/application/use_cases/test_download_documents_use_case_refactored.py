import os
import tempfile

import pytest

from datafinance.brazil.cvm.fundamental_stocks_data import (
    DownloadDocsCVMRepositoryCVM,
    DownloadDocumentsUseCaseCVM,
    DownloadResultCVM,
    InvalidDocName,
    InvalidFirstYear,
    InvalidRepositoryTypeError,
)


class MockRepository(DownloadDocsCVMRepositoryCVM):
    def __init__(self):
        self.download_docs_called = False
        self.last_tasks = None

    def download_docs(self, tasks: list) -> DownloadResultCVM:
        self.download_docs_called = True
        self.last_tasks = tasks

        return DownloadResultCVM(successful_downloads=["DFP_2020", "DFP_2021"])


@pytest.mark.unit
class TestDownloadDocumentsUseCaseOrchestration:
    def test_orchestrator_calls_repository(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2023,
        )

        assert mock_repo.download_docs_called
        assert mock_repo.last_tasks is not None
        assert isinstance(mock_repo.last_tasks, list)

    def test_orchestrator_passes_validated_data_to_repository(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP", "ITR"],
            initial_year=2020,
            last_year=2022,
        )

        assert mock_repo.last_tasks is not None
        assert len(mock_repo.last_tasks) >= 1
        for task in mock_repo.last_tasks:
            assert isinstance(task, tuple)
            assert len(task) == 4
            url, doc_name, year, dest_path = task
            assert isinstance(url, str)
            assert isinstance(doc_name, str)
            assert isinstance(year, str)
            assert isinstance(dest_path, str)

    def test_orchestrator_returns_download_result(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2023,
        )

        assert isinstance(result, DownloadResultCVM)
        assert result.success_count_downloads > 0

    def test_orchestrator_creates_directory_via_validator(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "new_dir")

            mock_repo = MockRepository()
            use_case = DownloadDocumentsUseCaseCVM(mock_repo)

            use_case.execute(
                destination_path=new_path,
                list_docs=["DFP"],
                initial_year=2020,
                last_year=2020,
            )

            assert os.path.exists(new_path)

    def test_orchestrator_generates_correct_tasks(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2021,
        )

        assert len(mock_repo.last_tasks) == 2

        for task in mock_repo.last_tasks:
            url, doc_name, year, dest_path = task
            assert "dados.cvm.gov.br" in url
            assert doc_name == "DFP"
            assert year in ["2020", "2021"]
            assert dest_path.startswith(str(tmp_path))

    def test_orchestrator_respects_year_constraints_for_itr(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["ITR"],
            initial_year=2010,
            last_year=2012,
        )

        assert len(mock_repo.last_tasks) == 2
        years_in_tasks = [task[2] for task in mock_repo.last_tasks]
        assert "2011" in years_in_tasks
        assert "2012" in years_in_tasks
        assert "2010" not in years_in_tasks

    def test_orchestrator_respects_year_constraints_for_cgvn(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["CGVN"],
            initial_year=2016,
            last_year=2019,
        )

        assert len(mock_repo.last_tasks) == 2
        years_in_tasks = [task[2] for task in mock_repo.last_tasks]
        assert "2018" in years_in_tasks
        assert "2019" in years_in_tasks
        assert "2016" not in years_in_tasks
        assert "2017" not in years_in_tasks


@pytest.mark.unit
class TestDownloadDocumentsUseCaseBackwardCompatibility:
    def test_same_interface_as_before(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2023,
        )

        assert isinstance(result, DownloadResultCVM)

    def test_handles_none_doc_types(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=None,
            initial_year=2020,
            last_year=2020,
        )

        assert isinstance(result, DownloadResultCVM)
        assert len(mock_repo.last_tasks) > 1

    def test_handles_none_years(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=None,
            last_year=None,
        )

        assert isinstance(result, DownloadResultCVM)
        assert mock_repo.download_docs_called

    def test_creates_directory_if_not_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "new_dir")

            mock_repo = MockRepository()
            use_case = DownloadDocumentsUseCaseCVM(mock_repo)

            use_case.execute(
                destination_path=new_path,
                list_docs=["DFP"],
                initial_year=2020,
                last_year=2020,
            )

            assert os.path.exists(new_path)


@pytest.mark.unit
class TestDownloadDocumentsUseCaseErrorHandling:
    def test_validation_error_stops_execution(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        with pytest.raises(InvalidDocName):
            use_case.execute(
                destination_path=str(tmp_path),
                list_docs=["INVALID"],
                initial_year=2020,
                last_year=2023,
            )

        assert not mock_repo.download_docs_called

    def test_invalid_year_error_stops_execution(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        with pytest.raises(InvalidFirstYear):
            use_case.execute(
                destination_path=str(tmp_path),
                list_docs=["DFP"],
                initial_year=1990,
                last_year=2020,
            )

        assert not mock_repo.download_docs_called

    def test_repository_error_is_propagated(self, tmp_path):
        class ErrorRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(self, tasks):
                raise RuntimeError("Download failed")

        error_repo = ErrorRepository()
        use_case = DownloadDocumentsUseCaseCVM(error_repo)

        with pytest.raises(RuntimeError, match="Download failed"):
            use_case.execute(
                destination_path=str(tmp_path),
                list_docs=["DFP"],
                initial_year=2020,
                last_year=2020,
            )


@pytest.mark.unit
class TestDownloadDocumentsUseCaseInitialization:
    def test_init_with_valid_repository(self):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        assert use_case is not None
        assert use_case._DownloadDocumentsUseCase__repository is mock_repo

    def test_init_with_invalid_repository_raises_error(self):
        with pytest.raises(
            InvalidRepositoryTypeError,
            match="The repository must be a valid repository instance",
        ):
            DownloadDocumentsUseCaseCVM("not a repository")

    def test_init_with_none_repository_raises_error(self):
        with pytest.raises(InvalidRepositoryTypeError):
            DownloadDocumentsUseCaseCVM(None)

    def test_init_creates_sub_use_cases(self):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        assert hasattr(use_case, "_DownloadDocumentsUseCase__url_generator")
        assert hasattr(use_case, "_DownloadDocumentsUseCase__range_years_generator")
        assert use_case._DownloadDocumentsUseCase__url_generator is not None
        assert use_case._DownloadDocumentsUseCase__range_years_generator is not None


@pytest.mark.unit
class TestDownloadDocumentsUseCaseLogging:
    def test_logs_orchestration_start(self, tmp_path, caplog):
        import logging

        caplog.set_level(logging.INFO)

        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2020,
        )

        assert any(
            "orchestration" in record.message.lower() for record in caplog.records
        )

    def test_logs_download_completion(self, tmp_path, caplog):
        import logging

        caplog.set_level(logging.INFO)

        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2020,
        )

        assert any("completed" in record.message.lower() for record in caplog.records)


@pytest.mark.unit
class TestDownloadDocumentsUseCaseIntegrationWithRealSubUseCases:
    def test_full_integration_with_real_sub_use_cases(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2022,
            last_year=2023,
        )

        assert isinstance(result, DownloadResultCVM)

        assert len(mock_repo.last_tasks) == 2

        for task in mock_repo.last_tasks:
            url, doc_name, year, dest_path = task
            assert "dados.cvm.gov.br" in url
            assert doc_name == "DFP"
            assert year in ["2022", "2023"]

    def test_integration_with_multiple_docs_and_years(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP", "ITR", "FRE"],
            initial_year=2020,
            last_year=2022,
        )

        assert isinstance(result, DownloadResultCVM)

        assert len(mock_repo.last_tasks) == 9

        doc_names = {task[1] for task in mock_repo.last_tasks}
        assert doc_names == {"DFP", "ITR", "FRE"}


@pytest.mark.unit
class TestDownloadDocumentsUseCaseTaskPreparation:
    def test_tasks_contain_correct_structure(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2020,
        )

        assert len(mock_repo.last_tasks) == 1
        task = mock_repo.last_tasks[0]

        assert isinstance(task, tuple)
        assert len(task) == 4

        url, doc_name, year, dest_path = task
        assert isinstance(url, str) and url.startswith("https://")
        assert isinstance(doc_name, str) and doc_name == "DFP"
        assert isinstance(year, str) and year == "2020"
        assert isinstance(dest_path, str) and os.path.isabs(dest_path)

    def test_tasks_match_years_from_docs_paths(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["ITR"],
            initial_year=2010,
            last_year=2012,
        )

        years_in_tasks = [task[2] for task in mock_repo.last_tasks]
        assert "2011" in years_in_tasks
        assert "2012" in years_in_tasks
        assert "2010" not in years_in_tasks
        assert len(years_in_tasks) == 2

    def test_tasks_urls_match_years(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2021,
        )

        for task in mock_repo.last_tasks:
            url, doc_name, year, dest_path = task
            assert year in url, f"Year {year} should be in URL {url}"

    def test_tasks_destination_paths_are_valid(self, tmp_path):
        """Destination paths in tasks should exist and be writable."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2021,
        )

        for task in mock_repo.last_tasks:
            url, doc_name, year, dest_path = task
            assert os.path.exists(dest_path)
            assert os.path.isdir(dest_path)
            assert os.access(dest_path, os.W_OK)

    def test_missing_url_for_year_logs_warning(self, tmp_path, caplog):
        """Should log warning when URL is missing for a year."""
        import logging

        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        with caplog.at_level(logging.WARNING):
            result = use_case.execute(
                destination_path=str(tmp_path),
                list_docs=["DFP"],
                initial_year=2020,
                last_year=2020,
            )

        assert isinstance(result, DownloadResultCVM)

    def test_tasks_with_all_document_types(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        all_docs = ["CGVN", "FRE", "FCA", "DFP", "ITR", "IPE", "VLMO"]

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=all_docs,
            initial_year=2020,
            last_year=2020,
        )

        doc_names_in_tasks = {task[1] for task in mock_repo.last_tasks}
        assert len(doc_names_in_tasks) >= 5

    def test_task_urls_contain_correct_doc_type(self, tmp_path):
        """URL should contain the correct document type identifier."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP", "ITR"],
            initial_year=2020,
            last_year=2020,
        )

        for task in mock_repo.last_tasks:
            url, doc_name, year, dest_path = task
            # URL should contain the doc name in lowercase
            assert doc_name.lower() in url.lower()

    def test_task_urls_end_with_zip(self, tmp_path):
        """All task URLs should end with .zip extension."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2021,
        )

        for task in mock_repo.last_tasks:
            url, doc_name, year, dest_path = task
            assert url.endswith(".zip")

    def test_tasks_for_multiple_years_ordered_correctly(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2018,
            last_year=2022,
        )

        dfp_years = [int(task[2]) for task in mock_repo.last_tasks if task[1] == "DFP"]

        assert len(dfp_years) == 5
        assert min(dfp_years) == 2018
        assert max(dfp_years) == 2022

    def test_tasks_preserve_absolute_paths(self, tmp_path):
        """All destination paths in tasks should be absolute."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2020,
        )

        for task in mock_repo.last_tasks:
            url, doc_name, year, dest_path = task
            assert os.path.isabs(dest_path)

    def test_empty_tasks_when_no_valid_years(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["CGVN"],
            initial_year=2010,
            last_year=2017,
        )

        assert isinstance(result, DownloadResultCVM)
        assert len(mock_repo.last_tasks) == 0

    def test_tasks_count_matches_valid_years_count(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCaseCVM(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP", "ITR"],
            initial_year=2020,
            last_year=2022,
        )

        assert len(mock_repo.last_tasks) == 6
