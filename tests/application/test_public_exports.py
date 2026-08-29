"""Tests for the package's public exports and version resolution."""

from __future__ import annotations

import ast
import importlib
import importlib.metadata
import importlib.util
import runpy
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / 'src'
EXPECTED_ROOT_EXPORTS = [
    'ExtractionResultB3',
    'FundamentalStocksDataCVM',
    'HistoricalQuotesB3',
    '__version__',
]
EXPORT_MODULES = (
    'globaldatafinance',
    'globaldatafinance._version',
    'globaldatafinance.application',
    'globaldatafinance.application.b3_docs',
    'globaldatafinance.application.b3_docs.result_formatters',
    'globaldatafinance.application.cvm_docs',
    'globaldatafinance.brazil.b3_data.historical_quotes',
    'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service',
    'globaldatafinance.brazil.b3_data.historical_quotes.parquet_writer',
    'globaldatafinance.brazil.cvm.fundamental_stocks_data',
    'globaldatafinance.core',
    'globaldatafinance.core.utils',
    'globaldatafinance.macro_exceptions',
    'globaldatafinance.macro_infra',
)


def _load_settings_from_directory(
    directory: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[int, bool]:
    saved_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == 'globaldatafinance' or name.startswith('globaldatafinance.')
    }
    saved_path = sys.path.copy()

    try:
        for name in saved_modules:
            del sys.modules[name]
        monkeypatch.chdir(directory)
        sys.path.insert(0, str(SOURCE_ROOT))

        importlib.import_module('globaldatafinance')
        config = importlib.import_module('globaldatafinance.core.config')
        settings = config.settings
        return settings.network.timeout, settings.debug
    finally:
        for name in list(sys.modules):
            if name == 'globaldatafinance' or name.startswith(
                'globaldatafinance.'
            ):
                del sys.modules[name]
        sys.modules.update(saved_modules)
        sys.path[:] = saved_path


def _clear_configuration_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        'DATAFINANCE_DEBUG',
        'DATAFINANCE_NETWORK',
        'DATAFINANCE_NETWORK_TIMEOUT',
        'DATAFINANCE_NETWORK_MAX_RETRIES',
        'DATAFINANCE_NETWORK_RETRY_BACKOFF',
        'DATAFINANCE_NETWORK_USER_AGENT',
    ):
        monkeypatch.delenv(name, raising=False)


def test_root_all_and_facade_identities() -> None:
    package = importlib.import_module('globaldatafinance')
    application = importlib.import_module('globaldatafinance.application')

    assert package.__all__ == EXPECTED_ROOT_EXPORTS
    assert package.ExtractionResultB3 is application.ExtractionResultB3
    assert (
        package.FundamentalStocksDataCVM
        is application.FundamentalStocksDataCVM
    )
    assert package.HistoricalQuotesB3 is application.HistoricalQuotesB3


def test_root_version_matches_installed_metadata() -> None:
    package = importlib.import_module('globaldatafinance')

    assert package.__version__ == importlib.metadata.version(
        'globaldatafinance'
    )


def test_version_module_uses_source_tree_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version_path = SOURCE_ROOT / 'globaldatafinance' / '_version.py'

    def missing_distribution(_: str) -> str:
        raise importlib.metadata.PackageNotFoundError('globaldatafinance')

    monkeypatch.setattr(importlib.metadata, 'version', missing_distribution)
    spec = importlib.util.spec_from_file_location(
        'globaldatafinance_test_version', version_path
    )
    if spec is None or spec.loader is None:
        pytest.fail(f'Unable to load version module from {version_path}')

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.__version__ == '0.2.0'


def test_root_import_works_without_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_configuration_environment(monkeypatch)

    assert _load_settings_from_directory(tmp_path, monkeypatch) == (180, False)


def test_root_import_ignores_dotenv_in_consumer_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / '.env').write_text(
        'DATAFINANCE_DEBUG=true\nDATAFINANCE_NETWORK_TIMEOUT=60\n',
        encoding='utf-8',
    )

    _clear_configuration_environment(monkeypatch)

    assert _load_settings_from_directory(tmp_path, monkeypatch) == (180, False)


@pytest.mark.parametrize('module_name', EXPORT_MODULES)
def test_declared_all_names_exist(module_name: str) -> None:
    module = importlib.import_module(module_name)
    exported_names = module.__dict__['__all__']

    assert isinstance(exported_names, list)
    assert all(hasattr(module, name) for name in exported_names)


@pytest.mark.parametrize('module_name', EXPORT_MODULES)
def test_star_import_exposes_only_declared_names(
    module_name: str, tmp_path: Path
) -> None:
    module = importlib.import_module(module_name)
    script_path = tmp_path / 'star_import_check.py'
    script_path.write_text(
        f'from {module_name} import *\n',
        encoding='utf-8',
    )

    namespace = runpy.run_path(str(script_path))

    imported_names = {
        name
        for name in namespace
        if not name.startswith('__') or name in module.__all__
    }
    assert imported_names == set(module.__all__)


def test_version_module_has_no_application_imports() -> None:
    version_source = (
        SOURCE_ROOT / 'globaldatafinance' / '_version.py'
    ).read_text(encoding='utf-8')
    tree = ast.parse(version_source)
    imported_modules = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    ]
    imported_modules.extend(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )

    assert all(
        not module_name.startswith('globaldatafinance')
        for module_name in imported_modules
    )
