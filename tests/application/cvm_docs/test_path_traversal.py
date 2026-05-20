import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data.client import (
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

    def test_scenario_error_path_traversal_usr(self):
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path='/usr/local/cvm',
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_scenario_error_path_traversal_var(self):
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path='/var/lib/malicious',
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_scenario_error_path_traversal_lib(self):
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path='/lib/cvm',
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_scenario_error_path_traversal_user_ssh(self):
        from pathlib import Path

        target = str(Path.home() / '.ssh' / 'cvm_dump')
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path=target,
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_scenario_error_path_traversal_user_aws(self):
        from pathlib import Path

        target = str(Path.home() / '.aws' / 'cvm_dump')
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path=target,
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_scenario_error_path_traversal_user_gnupg(self):
        from pathlib import Path

        target = str(Path.home() / '.gnupg' / 'cvm_dump')
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path=target,
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_scenario_error_path_traversal_windows_system(self):
        # Cross-platform: even on POSIX, Windows system paths must raise.
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path='C:\\Windows\\System32',
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_scenario_error_path_traversal_windows_program_files(self):
        with pytest.raises(SecurityError):
            use_case = VerifyPathsUseCasesCVM(
                destination_path='C:\\Program Files\\malicious',
                new_set_docs={'DFP'},
                range_years=range(2023, 2024),
            )
            use_case.execute()

    def test_etcd_directory_not_falsely_blocked(self, tmp_path):
        """Regression: the previous `startswith('/etc')` check would
        block `/etcd_data` as a false positive. After unification on
        the path-aware helper, such directories must be allowed.
        """
        etcd_dir = tmp_path / 'etcd_data'
        use_case = VerifyPathsUseCasesCVM(
            destination_path=str(etcd_dir),
            new_set_docs={'DFP'},
            range_years=range(2023, 2024),
        )
        result = use_case.execute()
        assert 'DFP' in result

    def test_development_directory_not_falsely_blocked(self, tmp_path):
        """Regression: `/development*` was blocked by the prior /dev
        startswith check; the path-aware helper must accept it.
        """
        dev_dir = tmp_path / 'development'
        use_case = VerifyPathsUseCasesCVM(
            destination_path=str(dev_dir),
            new_set_docs={'DFP'},
            range_years=range(2023, 2024),
        )
        result = use_case.execute()
        assert 'DFP' in result
