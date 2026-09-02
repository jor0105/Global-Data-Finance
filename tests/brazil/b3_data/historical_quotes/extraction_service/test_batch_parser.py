import pytest

from globaldatafinance.brazil.b3_data.historical_quotes import (
    CotahistParserB3,
    extraction_service,
)
from tests.brazil.b3_data.historical_quotes.conftest import build_cotahist_line

pytestmark = pytest.mark.unit

parse_lines_batch = extraction_service.batch_parser.parse_lines_batch


def test_parse_lines_batch_filters_by_target() -> None:
    lines = [build_cotahist_line('010'), build_cotahist_line('020')]

    records = parse_lines_batch(lines, {'010'})

    assert len(records) == 1
    assert records[0]['tipo_mercado'] == '010'


def test_parse_lines_batch_matches_sequential_parser() -> None:
    lines = [
        '00COTAHIST' + ' ' * 235,
        build_cotahist_line('010'),
        build_cotahist_line('020'),
        '01' + '20230615' + '02' + 'PETR4       ' + '010' + ' ' * 217,
        '0120230615',
        '99TRAILER' + ' ' * 235,
    ]
    target_codes = {'010'}

    batch_records = parse_lines_batch(lines, target_codes)
    sequential_parser = CotahistParserB3()
    sequential_records = [
        record
        for record in (
            sequential_parser.parse_line(line, target_codes) for line in lines
        )
        if record is not None
    ]

    assert batch_records == sequential_records
