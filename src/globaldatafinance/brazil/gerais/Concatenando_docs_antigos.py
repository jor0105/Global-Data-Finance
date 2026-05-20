from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .url_e_nomes import (
    lista_atual,
    nomes_arquivos_cgvn,
    nomes_arquivos_fca,
    nomes_arquivos_fre,
    nomes_arquivos_vlmo,
)

LOGGER = logging.getLogger(__name__)

FrameNormalizer = Callable[..., pd.DataFrame]
NumericNormalizer = Callable[[pd.DataFrame], pd.DataFrame]
CodigoMap = Mapping[str, Any]


def _identity_frame_normalizer(
    data: pd.DataFrame,
    *,
    reverter: bool = False,
) -> pd.DataFrame:
    return data


def _identity_numeric_normalizer(data: pd.DataFrame) -> pd.DataFrame:
    return data


def _resolve_yearly_directory(
    output_directory: Path,
    yearly_directory: str | Path | None,
) -> Path:
    if yearly_directory is not None:
        return Path(yearly_directory)

    conventional_years_directory = output_directory / 'anos'
    if conventional_years_directory.exists():
        return conventional_years_directory

    return output_directory


def _read_yearly_parquet(
    yearly_directory: Path,
    file_prefix: str,
    year: int,
) -> pd.DataFrame | None:
    parquet_path = yearly_directory / f'{file_prefix}{year}.parquet'
    try:
        data = pd.read_parquet(parquet_path)
    except FileNotFoundError:
        return None

    if data.empty:
        return None

    return data


def _concat_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def _write_consolidated_parquet(
    data: pd.DataFrame,
    output_directory: Path,
    file_prefix: str,
    start_year: int,
    end_year: int,
) -> None:
    output_path = (
        output_directory / f'{file_prefix}{start_year}-{end_year}.parquet'
    )
    data.to_parquet(output_path)


def _require_codigo_maps(
    cnpj_to_codigo: CodigoMap | None,
    nome_to_codigo: CodigoMap | None,
) -> tuple[CodigoMap, CodigoMap]:
    if cnpj_to_codigo is None or nome_to_codigo is None:
        raise ValueError(
            'cnpj_to_codigo and nome_to_codigo are required to consolidate '
            'legacy CVM documents.'
        )

    return cnpj_to_codigo, nome_to_codigo


def _enrich_codigo_from_issuer(
    data: pd.DataFrame,
    *,
    cnpj_column: str,
    fallback_name_column: str,
    cnpj_to_codigo: CodigoMap,
    nome_to_codigo: CodigoMap,
    drop_columns: list[str],
) -> pd.DataFrame:
    data = data.copy()
    data['Código'] = 0
    data[cnpj_column] = data[cnpj_column].str.replace(
        r'\D',
        '',
        regex=True,
    )
    data['Código'] = data[cnpj_column].map(cnpj_to_codigo)
    missing_codigo = data['Código'].isna()
    data.loc[missing_codigo, 'Código'] = data.loc[
        missing_codigo,
        fallback_name_column,
    ].map(nome_to_codigo)
    data = data.dropna(subset=['Código'])
    return data.drop(drop_columns, axis=1)


def _format_brazilian_decimal(value: Any, decimals: int) -> str:
    if pd.isna(value):
        return ''

    return (
        f'{float(value):,.{decimals}f}'.replace(',', 'v')
        .replace('.', ',')
        .replace('v', '.')
    )


def _format_brazilian_percentage(
    value: Any,
    decimals: int = 2,
    *,
    max_value: float | None = None,
) -> str:
    if pd.isna(value):
        return ''

    numeric_value = float(str(value).replace(',', '.'))
    if max_value is not None and numeric_value >= max_value:
        return ''

    return f'{numeric_value:.{decimals}f}%'


def _format_decimal_percentage(
    value: Any,
    decimals: int = 1,
    *,
    max_value: float | None = None,
) -> str:
    formatted = _format_brazilian_decimal(value, decimals)
    if not formatted:
        return ''

    if max_value is not None and float(value) >= max_value:
        return ''

    return f'{formatted}%'


def _keep_two_latest_reference_dates(data: pd.DataFrame) -> pd.DataFrame:
    unique_dates = data['Data_Referencia'].dropna().unique()
    unique_dates = sorted(unique_dates, reverse=True)
    if len(unique_dates) < 2:
        return data

    return data[data['Data_Referencia'] >= unique_dates[1]]


def _normalize_frame(
    data: pd.DataFrame,
    normalizer: FrameNormalizer,
    *,
    reverter: bool = False,
) -> pd.DataFrame:
    return normalizer(data, reverter=reverter)


def _prepare_cgvn_frame(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data = data.drop(['Versao', 'ID_Documento'], axis=1)
    data['Data_Referencia'] = pd.to_datetime(
        data['Data_Referencia'],
        errors='coerce',
    )
    return data


def _prepare_vlmo_frame(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data = data.drop(['Versao', 'Preco_Unitario', 'Volume'], axis=1)
    data['Data_Movimentacao'] = pd.to_datetime(
        data['Data_Movimentacao'],
        errors='coerce',
    )
    return data


def _prepare_fca_frame(name: str, data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data['Data_Referencia'] = pd.to_datetime(
        data['Data_Referencia'],
        errors='coerce',
    )

    if name == 'fca_cia_aberta_geral_':
        data = data.drop(
            [
                'Data_Nome_Empresarial',
                'Data_Categoria_Registro_CVM',
                'Situacao_Registro_CVM',
                'Data_Situacao_Registro_CVM',
                'Data_Situacao_Emissor',
                'Data_Especie_Controle_Acionario',
                'Data_Alteracao_Exercicio_Social',
            ],
            axis=1,
        )
    elif name == 'fca_cia_aberta_valor_mobiliario_':
        data = data.drop(
            [
                'Sigla_Classe_Acao_Preferencial',
                'Classe_Acao_Preferencial',
                'Sigla_Entidade_Administradora',
                'Data_Fim_Negociacao',
            ],
            axis=1,
        )
    elif name == 'fca_cia_aberta_canal_divulgacao_':
        data = _keep_latest_version(
            data,
            subset=['Canal_Divulgacao', 'Data_Referencia'],
        )
        data = data.drop(['Versao', 'Sigla_UF'], axis=1)
    elif name == 'fca_cia_aberta_endereco_':
        data = _keep_latest_version(
            data, subset=['Tipo_Endereco', 'Complemento']
        )
        data = data.drop(
            ['Versao', 'Caixa_Postal', 'DDI_Fax', 'DDD_Fax', 'Fax'],
            axis=1,
        )

    return data.drop('ID_Documento', axis=1)


def _keep_latest_version(
    data: pd.DataFrame,
    *,
    subset: list[str],
) -> pd.DataFrame:
    data = data.copy()
    data['Versao'] = pd.to_numeric(data['Versao'], errors='coerce')
    data = data.sort_values(by='Versao', ascending=False)
    return data.drop_duplicates(subset=subset, keep='first')


def _prepare_participacao_sociedade(data: pd.DataFrame) -> pd.DataFrame:
    data = data[
        [
            'Data_Referencia',
            'CNPJ_Companhia',
            'Nome_Companhia',
            'Razao_Social',
            'CNPJ',
            'Participacao_Emissor',
        ]
    ].copy()
    data['CNPJ'] = data['CNPJ'].astype(str)
    data['Participacao_Emissor'] = data['Participacao_Emissor'].apply(
        _format_brazilian_percentage
    )
    return data


def _prepare_capital_social(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data = data.drop(['ID_Capital_Social', 'Prazo_Integralizacao'], axis=1)
    data['Quantidade_Acoes_Ordinarias'] = data[
        'Quantidade_Acoes_Ordinarias'
    ].astype(float)
    data['Quantidade_Acoes_Preferenciais'] = data[
        'Quantidade_Acoes_Preferenciais'
    ].astype(float)
    data['Quantidade_Total_Acoes'] = data['Quantidade_Total_Acoes'].astype(
        float
    )
    data['Data_Referencia'] = pd.to_datetime(
        data['Data_Referencia'],
        errors='coerce',
    )
    data['Data_Autorizacao_Aprovacao'] = pd.to_datetime(
        data['Data_Autorizacao_Aprovacao'],
        errors='coerce',
    )
    data['Valor_Capital'] = data['Valor_Capital'].astype(float)
    data['Quantidade_Total_Acoes'] = (
        data['Quantidade_Acoes_Ordinarias']
        + data['Quantidade_Acoes_Preferenciais']
    )
    newer_approval = (
        data['Data_Referencia'] < data['Data_Autorizacao_Aprovacao']
    )
    data.loc[newer_approval, 'Data_Referencia'] = data.loc[
        newer_approval,
        'Data_Autorizacao_Aprovacao',
    ]
    return data


def _prepare_distribuicao_capital(data: pd.DataFrame) -> pd.DataFrame:
    data = data[
        [
            'CNPJ_Companhia',
            'Data_Referencia',
            'Nome_Companhia',
            'Quantidade_Acionistas_PF',
            'Quantidade_Acionistas_PJ',
            'Quantidade_Acionistas_Investidores_Institucionais',
            'Percentual_Acoes_Ordinarias_Circulacao',
            'Percentual_Acoes_Preferenciais_Circulacao',
            'Percentual_Total_Acoes_Circulacao',
            'Data_Ultima_Assembleia',
        ]
    ].copy()
    data['Total de Investidores'] = (
        data['Quantidade_Acionistas_PJ']
        + data['Quantidade_Acionistas_PF']
        + data['Quantidade_Acionistas_Investidores_Institucionais']
    )
    percentage_columns = [
        'Percentual_Acoes_Ordinarias_Circulacao',
        'Percentual_Acoes_Preferenciais_Circulacao',
        'Percentual_Total_Acoes_Circulacao',
    ]
    for column in percentage_columns:
        data[column] = data[column].apply(_format_brazilian_percentage)
    return data


def _prefer_related_shareholder_value(
    row: pd.Series,
    *,
    current_column: str,
    related_column: str,
    only_when_current_in: set[str] | None = None,
) -> Any:
    related_value = row[related_column]
    current_value = row[current_column]
    if pd.isna(related_value) or str(related_value).strip() == '':
        return current_value

    if (
        only_when_current_in is not None
        and current_value not in only_when_current_in
    ):
        return current_value

    return related_value


def _format_decimal_percentage_max_100(value: Any) -> str:
    return _format_decimal_percentage(value, decimals=1, max_value=100)


def _format_decimal_percentage_one_decimal(value: Any) -> str:
    return _format_decimal_percentage(value, decimals=1)


def _format_brazilian_decimal_two(value: Any) -> str:
    return _format_brazilian_decimal(value, decimals=2)


def _prefer_acionista_value(row: pd.Series) -> Any:
    return _prefer_related_shareholder_value(
        row,
        current_column='Acionista',
        related_column='Acionista_Relacionado',
        only_when_current_in={'Outros', 'Ações Tesouraria'},
    )


def _prefer_cpf_cnpj_acionista_value(row: pd.Series) -> Any:
    return _prefer_related_shareholder_value(
        row,
        current_column='CPF_CNPJ_Acionista',
        related_column='CPF_CNPJ_Acionista_Relacionado',
    )


def _prefer_tipo_pessoa_acionista_value(row: pd.Series) -> Any:
    return _prefer_related_shareholder_value(
        row,
        current_column='Tipo_Pessoa_Acionista',
        related_column='Tipo_Pessoa_Acionista_Relacionado',
    )


def _prepare_posicao_acionaria(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data.fillna(np.nan, inplace=True)
    for column in [
        'Quantidade_Acao_Ordinaria_Circulacao',
        'Quantidade_Acao_Preferencial_Circulacao',
        'Quantidade_Total_Acoes_Circulacao',
    ]:
        data[column] = (
            data[column]
            .astype(str)
            .str.replace(r'\.', '', regex=True)
            .str.replace(',', '.', regex=False)
            .astype(float)
        )

    data = data[data['Quantidade_Total_Acoes_Circulacao'] > 0]
    data['Percentual_Total_Acoes_Circulacao'] = data[
        'Percentual_Total_Acoes_Circulacao'
    ].apply(_format_decimal_percentage_max_100)
    data = data[data['Percentual_Total_Acoes_Circulacao'] != '']
    data['Percentual_Acao_Ordinaria_Circulacao'] = data[
        'Percentual_Acao_Ordinaria_Circulacao'
    ].apply(_format_decimal_percentage_one_decimal)
    data['Percentual_Acao_Preferencial_Circulacao'] = data[
        'Percentual_Acao_Preferencial_Circulacao'
    ].apply(_format_decimal_percentage_one_decimal)
    data['Acionista'] = data.apply(_prefer_acionista_value, axis=1)
    data['CPF_CNPJ_Acionista'] = data.apply(
        _prefer_cpf_cnpj_acionista_value,
        axis=1,
    )
    data['Tipo_Pessoa_Acionista'] = data.apply(
        _prefer_tipo_pessoa_acionista_value,
        axis=1,
    )
    data['Versao'] = pd.to_numeric(data['Versao'], errors='coerce')
    data = data.sort_values(by='Versao', ascending=False)
    return data.drop(
        [
            'ID_Acionista',
            'ID_Documento',
            'ID_Acionista_Relacionado',
            'Sigla_UF',
            'Versao',
            'Acionista_Relacionado',
            'Tipo_Pessoa_Acionista_Relacionado',
            'CPF_CNPJ_Acionista_Relacionado',
        ],
        axis=1,
    ).drop_duplicates()


def _prepare_fre_frame(name: str, data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    if 'Descricao_Outro_Cargo_Ocupado' in data.columns:
        data['Descricao_Outro_Cargo_Ocupado'] = data[
            'Descricao_Outro_Cargo_Ocupado'
        ].astype(str)

    if name == 'fre_cia_aberta_membro_comite_':
        data['Percentual_Participacao_Reunioes'] = pd.to_numeric(
            data['Percentual_Participacao_Reunioes'],
            errors='coerce',
        )
        return data.drop(
            ['Descricao_Outro_Cargo_Ocupado', 'Data_Nascimento'],
            axis=1,
        )
    if name == 'fre_cia_aberta_membro_comite_auditor_':
        data['Data_Nascimento'] = pd.to_datetime(
            data['Data_Nascimento'],
            errors='coerce',
        )
        return data.drop(['Descricao_Outro_Cargo_Ocupado'], axis=1)
    if name == 'fre_cia_aberta_remuneracao_total_orgao_':
        data['Data_Fim_Exercicio_Social'] = pd.to_datetime(
            data['Data_Fim_Exercicio_Social']
        )
        data = data.drop('Data_Referencia', axis=1)
        data = data[
            pd.to_numeric(
                data['Numero_Membros_Remunerados'],
                errors='coerce',
            )
            > 0
        ]
        data = data.sort_values(
            by='Data_Fim_Exercicio_Social',
            ascending=False,
        )
        data['Data_Fim_Exercicio_Social'] = data[
            'Data_Fim_Exercicio_Social'
        ].dt.strftime('%Y-%m-%d')
        return data
    if name == 'fre_cia_aberta_titulo_exterior_':
        data['Data_Vencimento'] = pd.to_datetime(
            data['Data_Vencimento'],
            errors='coerce',
        )
        today = pd.to_datetime(datetime.today().date())
        data = data[data['Data_Vencimento'] >= today]
        data = data.drop('Data_Referencia', axis=1)
        data['Data_Vencimento'] = data['Data_Vencimento'].dt.strftime(
            '%Y-%m-%d'
        )
        return data
    if name == 'fre_cia_aberta_capital_social_titulo_conversivel_':
        return data.drop(['ID_Capital_Social'], axis=1)
    if name == 'fre_cia_aberta_participacao_sociedade_':
        return _prepare_participacao_sociedade(data)
    if name == 'fre_cia_aberta_auditor_':
        return data.drop(['ID_Auditor'], axis=1)
    if name == 'fre_cia_aberta_capital_social_':
        return _prepare_capital_social(data)
    if name == 'fre_cia_aberta_distribuicao_capital_':
        return _prepare_distribuicao_capital(data)
    if name == 'fre_cia_aberta_posicao_acionaria_':
        return _prepare_posicao_acionaria(data)
    if name == 'fre_cia_aberta_capital_social_aumento_':
        return data.drop(['ID_Capital_Social_Aumento'], axis=1)

    return data


def _collect_transformed_frames(
    *,
    yearly_directory: Path,
    file_prefix: str,
    start_year: int,
    end_year_exclusive: int,
    transform: Callable[[pd.DataFrame], pd.DataFrame],
) -> pd.DataFrame:
    frames = []
    for year in range(start_year, end_year_exclusive):
        frame = _read_yearly_parquet(yearly_directory, file_prefix, year)
        if frame is not None:
            frames.append(transform(frame))

    return _concat_frames(frames)


def _consolidate_cgvn(
    *,
    output_directory: Path,
    yearly_directory: Path,
    start_year: int,
    end_year: int,
    end_year_exclusive: int,
    cgvn_start_year: int,
    cnpj_to_codigo: CodigoMap | None,
    nome_to_codigo: CodigoMap | None,
) -> None:
    data = _collect_transformed_frames(
        yearly_directory=yearly_directory,
        file_prefix=nomes_arquivos_cgvn,
        start_year=cgvn_start_year,
        end_year_exclusive=end_year_exclusive,
        transform=_prepare_cgvn_frame,
    )
    if data.empty:
        return

    cnpj_map, nome_map = _require_codigo_maps(cnpj_to_codigo, nome_to_codigo)
    data = _enrich_codigo_from_issuer(
        data,
        cnpj_column='CNPJ_Companhia',
        fallback_name_column='Nome_Empresarial',
        cnpj_to_codigo=cnpj_map,
        nome_to_codigo=nome_map,
        drop_columns=['Nome_Empresarial', 'CNPJ_Companhia'],
    )
    data = data.sort_values(by='Data_Referencia', ascending=False)
    data['Data_Referencia'] = data['Data_Referencia'].dt.strftime('%Y-%m-%d')
    _write_consolidated_parquet(
        data,
        output_directory,
        nomes_arquivos_cgvn,
        start_year,
        end_year,
    )
    LOGGER.info('Arquivos CGVN foram organizados.')


def _consolidate_vlmo(
    *,
    output_directory: Path,
    yearly_directory: Path,
    start_year: int,
    end_year: int,
    end_year_exclusive: int,
    cgvn_start_year: int,
    cnpj_to_codigo: CodigoMap | None,
    nome_to_codigo: CodigoMap | None,
) -> None:
    data = _collect_transformed_frames(
        yearly_directory=yearly_directory,
        file_prefix=nomes_arquivos_vlmo,
        start_year=cgvn_start_year,
        end_year_exclusive=end_year_exclusive,
        transform=_prepare_vlmo_frame,
    )
    if data.empty:
        LOGGER.info(
            'Arquivos VLMO não foram organizados pois não existem dados até '
            'a data detalhada.'
        )
        return

    cnpj_map, nome_map = _require_codigo_maps(cnpj_to_codigo, nome_to_codigo)
    data = _enrich_codigo_from_issuer(
        data,
        cnpj_column='CNPJ_Companhia',
        fallback_name_column='Empresa',
        cnpj_to_codigo=cnpj_map,
        nome_to_codigo=nome_map,
        drop_columns=['CNPJ_Companhia', 'Data_Referencia'],
    )
    data = data.sort_values(by='Data_Movimentacao', ascending=False)
    data['Quantidade'] = data['Quantidade'].apply(
        _format_brazilian_decimal_two
    )
    _write_consolidated_parquet(
        data,
        output_directory,
        nomes_arquivos_vlmo,
        start_year,
        end_year,
    )
    LOGGER.info('Arquivos VLMO foram organizados.')


def _build_fca_transform(
    name: str,
) -> Callable[[pd.DataFrame], pd.DataFrame]:
    def _transform(frame: pd.DataFrame) -> pd.DataFrame:
        return _prepare_fca_frame(name, frame)

    return _transform


def _build_fre_transform(
    name: str,
    normalizer: FrameNormalizer,
) -> Callable[[pd.DataFrame], pd.DataFrame]:
    def _transform(frame: pd.DataFrame) -> pd.DataFrame:
        return _normalize_frame(
            _prepare_fre_frame(name, frame),
            normalizer,
        )

    return _transform


def _consolidate_fca(
    *,
    output_directory: Path,
    yearly_directory: Path,
    start_year: int,
    end_year: int,
    end_year_exclusive: int,
    itr_start_year: int,
    cnpj_to_codigo: CodigoMap | None,
    nome_to_codigo: CodigoMap | None,
    normalizer: FrameNormalizer,
) -> None:
    for name in nomes_arquivos_fca:
        data = _collect_transformed_frames(
            yearly_directory=yearly_directory,
            file_prefix=name,
            start_year=itr_start_year,
            end_year_exclusive=end_year_exclusive,
            transform=_build_fca_transform(name),
        )
        if data.empty:
            continue

        cnpj_map, nome_map = _require_codigo_maps(
            cnpj_to_codigo,
            nome_to_codigo,
        )
        data = _normalize_frame(data, normalizer, reverter=True)
        if name in [
            'fca_cia_aberta_canal_divulgacao_',
            'fca_cia_aberta_endereco_',
        ]:
            data = _keep_two_latest_reference_dates(data)
        data = _enrich_codigo_from_issuer(
            data,
            cnpj_column='CNPJ_Companhia',
            fallback_name_column='Nome_Empresarial',
            cnpj_to_codigo=cnpj_map,
            nome_to_codigo=nome_map,
            drop_columns=['CNPJ_Companhia'],
        )
        data = data.sort_values(by='Data_Referencia', ascending=False)
        _write_consolidated_parquet(
            data,
            output_directory,
            name,
            start_year,
            end_year,
        )

    LOGGER.info('Arquivos FCA foram organizados.')


def _consolidate_fre(
    *,
    output_directory: Path,
    yearly_directory: Path,
    start_year: int,
    end_year: int,
    end_year_exclusive: int,
    itr_start_year: int,
    cnpj_to_codigo: CodigoMap | None,
    nome_to_codigo: CodigoMap | None,
    normalizer: FrameNormalizer,
    numeric_normalizer: NumericNormalizer,
) -> None:
    for name in nomes_arquivos_fre:
        data = _collect_transformed_frames(
            yearly_directory=yearly_directory,
            file_prefix=name,
            start_year=itr_start_year,
            end_year_exclusive=end_year_exclusive,
            transform=_build_fre_transform(name, normalizer),
        )
        if name in lista_atual:
            data = _normalize_frame(data, normalizer, reverter=True)

        try:
            if data.empty:
                continue

            if name in ['fre_cia_aberta_relacao_familiar_']:
                data = _keep_two_latest_reference_dates(data)

            cnpj_map, nome_map = _require_codigo_maps(
                cnpj_to_codigo,
                nome_to_codigo,
            )
            data = _enrich_codigo_from_issuer(
                data,
                cnpj_column='CNPJ_Companhia',
                fallback_name_column='Nome_Companhia',
                cnpj_to_codigo=cnpj_map,
                nome_to_codigo=nome_map,
                drop_columns=['Nome_Companhia', 'CNPJ_Companhia'],
            )
            data = numeric_normalizer(data)
            _write_consolidated_parquet(
                data,
                output_directory,
                name,
                start_year,
                end_year,
            )
        except (KeyError, TypeError, ValueError) as exc:
            LOGGER.exception('Erro ao salvar: %s | Erro: %s', name, exc)

    LOGGER.info('Arquivos FRE foram organizados.')


def concatenar_docs(
    diretorio: str | Path,
    diretorio_b3: str | Path | None,
    ano_inicial: int,
    ano_final: int,
    ano_cgvn: int = 2018,
    ano_ipe: int = 2024,
    novos: bool = False,
    *,
    yearly_directory: str | Path | None = None,
    output_directory: str | Path | None = None,
    cnpj_to_codigo: CodigoMap | None = None,
    nome_to_codigo: CodigoMap | None = None,
    itr_start_year: int | None = None,
    end_year_exclusive: int | None = None,
    frame_normalizer: FrameNormalizer | None = None,
    numeric_normalizer: NumericNormalizer | None = None,
) -> None:
    output_dir = Path(output_directory or diretorio)
    yearly_dir = _resolve_yearly_directory(output_dir, yearly_directory)
    normalizer = frame_normalizer or _identity_frame_normalizer
    value_normalizer = numeric_normalizer or _identity_numeric_normalizer
    itr_start = itr_start_year or ano_inicial
    final_year_exclusive = end_year_exclusive or (ano_final + 1)

    # Preserved for signature compatibility with the legacy script.
    _ = (diretorio_b3, ano_ipe, novos)

    _consolidate_cgvn(
        output_directory=output_dir,
        yearly_directory=yearly_dir,
        start_year=ano_inicial,
        end_year=ano_final,
        end_year_exclusive=final_year_exclusive,
        cgvn_start_year=ano_cgvn,
        cnpj_to_codigo=cnpj_to_codigo,
        nome_to_codigo=nome_to_codigo,
    )
    _consolidate_vlmo(
        output_directory=output_dir,
        yearly_directory=yearly_dir,
        start_year=ano_inicial,
        end_year=ano_final,
        end_year_exclusive=final_year_exclusive,
        cgvn_start_year=ano_cgvn,
        cnpj_to_codigo=cnpj_to_codigo,
        nome_to_codigo=nome_to_codigo,
    )
    _consolidate_fca(
        output_directory=output_dir,
        yearly_directory=yearly_dir,
        start_year=ano_inicial,
        end_year=ano_final,
        end_year_exclusive=final_year_exclusive,
        itr_start_year=itr_start,
        cnpj_to_codigo=cnpj_to_codigo,
        nome_to_codigo=nome_to_codigo,
        normalizer=normalizer,
    )
    _consolidate_fre(
        output_directory=output_dir,
        yearly_directory=yearly_dir,
        start_year=ano_inicial,
        end_year=ano_final,
        end_year_exclusive=final_year_exclusive,
        itr_start_year=itr_start,
        cnpj_to_codigo=cnpj_to_codigo,
        nome_to_codigo=nome_to_codigo,
        normalizer=normalizer,
        numeric_normalizer=value_normalizer,
    )
