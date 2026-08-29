"""Polars schema overrides for decimal-valued B3 quote columns."""

from typing import Any


def get_schema_overrides(polars_module: Any) -> dict[str, Any]:
    """Return fixed-precision decimal types for numeric quote fields."""
    return {
        'preco_abertura': polars_module.Decimal(precision=38, scale=2),
        'preco_maximo': polars_module.Decimal(precision=38, scale=2),
        'preco_minimo': polars_module.Decimal(precision=38, scale=2),
        'preco_medio': polars_module.Decimal(precision=38, scale=2),
        'preco_fechamento': polars_module.Decimal(precision=38, scale=2),
        'melhor_oferta_compra': polars_module.Decimal(precision=38, scale=2),
        'melhor_oferta_venda': polars_module.Decimal(precision=38, scale=2),
        'volume_total': polars_module.Decimal(precision=38, scale=2),
    }
