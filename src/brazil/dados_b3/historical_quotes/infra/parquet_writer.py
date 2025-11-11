from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import polars as pl
except ImportError:
    pl = None  # type: ignore

from src.macro_exceptions import DiskFullError


class ParquetWriter:
    """Writer for saving data to Parquet format using Polars.

    Raises:
        ImportError: If polars is not installed
    """

    def __init__(self):
        if pl is None:
            raise ImportError(
                "polars is required for ParquetWriter. "
                "Install it with: pip install polars"
            )

    async def write_to_parquet(
        self,
        data: List[Dict[str, Any]],
        output_path: Path,
        partition_cols: Optional[List[str]] = None,
    ) -> None:
        """Write data to Parquet format.

        Args:
            data: List of dictionaries containing parsed quote data
            output_path: Path where to save the Parquet file(s)
            partition_cols: Optional list of columns to partition by

        Raises:
            IOError: If unable to write to disk
            DiskFullError: If insufficient disk space
        """
        if not data:
            return

        try:
            # Convert list of dicts to Polars DataFrame
            df = pl.DataFrame(data)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write parquet file
            df.write_parquet(str(output_path))

        except OSError as e:
            if "No space left on device" in str(e):
                raise DiskFullError(str(output_path))
            raise IOError(f"Failed to write Parquet file: {e}")
