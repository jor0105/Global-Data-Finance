from typing import Dict

from ......core import get_logger
from ...domain import AvailableDocsCVM

logger = get_logger(__name__)


class GetAvailableDocsUseCaseCVM:
    """Use case for retrieving available CVM document types."""

    def __init__(self) -> None:
        """Initialize the use case."""
        self.__available_docs = AvailableDocsCVM()
        logger.debug("GetAvailableDocsUseCaseCVM initialized")

    def execute(self) -> Dict[str, str]:
        """Retrieve available document types.

        Returns:
            Dictionary mapping document codes to their descriptions.
        """
        logger.info("Retrieving available document types")

        try:
            docs = self.__available_docs.get_available_docs()
            logger.debug(f"Retrieved {len(docs)} document types")
            return docs
        except Exception as e:
            logger.error(f"Failed to retrieve available documents: {e}")
            raise
