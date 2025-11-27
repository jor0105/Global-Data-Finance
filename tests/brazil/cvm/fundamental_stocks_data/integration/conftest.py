import sys
from pathlib import Path

import pytest

src_path = Path(__file__).parent.parent.parent / 'globaldatafinance'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope='session')
def tmp_path_factory_session(tmp_path_factory):
    return tmp_path_factory


@pytest.fixture(autouse=True)
def setup_logging():
    from globaldatafinance.core import setup_logging

    setup_logging(level='WARNING')
