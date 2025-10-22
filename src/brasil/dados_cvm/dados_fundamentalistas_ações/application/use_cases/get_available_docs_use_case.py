import logging
from typing import Dict

from ...domain import AvailableDocs

logger = logging.getLogger(__name__)


class GetAvailableDocsUseCase:
    """Use case for retrieving available CVM document types.

    This use case provides information about all available document types
    that can be downloaded from CVM, such as DFP, ITR, FRE, etc.

    Example:
        >>> use_case = GetAvailableDocsUseCase()
        >>> docs = use_case.execute()
        >>> print(docs)
        {'DFP': 'Demonstração Financeira Padronizada', ...}
    """

    def __init__(self) -> None:
        """Initialize the use case with available documents data source."""
        self._available_docs = AvailableDocs()
        logger.debug("GetAvailableDocsUseCase initialized")

    def execute(self) -> Dict[str, str]:
        """Retrieve available document types.

        Returns:
            Dictionary mapping document codes to their descriptions.
            Example: {'DFP': 'Demonstração Financeira Padronizada', ...}

        Raises:
            Exception: If unable to retrieve available documents.
        """
        logger.info("Retrieving available document types")

        try:
            docs = self._available_docs.get_available_docs()
            logger.debug(f"Retrieved {len(docs)} document types")
            return docs
        except Exception as e:
            logger.error(f"Failed to retrieve available documents: {e}")
            raise
