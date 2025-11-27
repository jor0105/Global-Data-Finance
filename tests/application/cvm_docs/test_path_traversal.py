import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data.application.use_cases.verify_paths_use_cases import (
    VerifyPathsUseCasesCVM,
)
from globaldatafinance.macro_exceptions import SecurityError


@pytest.mark.unit
class TestVerifyPathsUseCasesCVM:
    def test_scenario_success_normal_path(self, tmp_path):
        destination_path = str(tmp_path / 'cvm_data')
        use_case = VerifyPathsUseCasesCVM(
            destination_path=destination_path,
            new_set_docs={'DFP'},
            range_years=range(2023, 2024),
        )

        result = use_case.execute()

        assert 'DFP' in result
        assert 2023 in result['DFP']

    def test_scenario_error_path_traversal_etc(self):
        with pytest.raises(SecurityError) as exc_info:
            use_case = VerifyPathsUseCasesCVM(
                destination_path='/etc/malicious',
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

        assert 'sensitive system directory' in str(exc_info.value)

    def test_scenario_error_path_traversal_sys(self):
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path='/sys/evil',
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_scenario_error_path_traversal_proc(self):
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path='/proc/malicious',
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_scenario_error_path_traversal_dev(self):
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path='/dev/null_folder',
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_scenario_error_path_traversal_boot(self):
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path='/boot/malware',
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_scenario_error_path_traversal_root(self):
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path='/root/.hidden',
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()
