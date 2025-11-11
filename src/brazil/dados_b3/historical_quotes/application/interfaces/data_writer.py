from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


class IDataWriter(Protocol):
    """Interface for writing extracted data to storage."""

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
            partition_cols: Optional list of columns to partition by (e.g., ['year', 'asset_class'])

        Raises:
            IOError: If unable to write to disk
        """
        ...
