from typing import Dict, List, Optional, Set, Tuple

from ..exceptions import InvalidDocName, InvalidTypeDoc


class AvailableDocsCVM:
    """Manages information about available CVM document types."""

    __DICT_AVAILABLE_DOCS: Dict[str, str] = {
        "CGVN": "(Governance Code Report) a periodic document that records information about adherence/compatibility with the Corporate Governance Code for publicly traded companies — governance structure, committees, policies, and relevant indicators.",
        "FRE": "(Reference Form) an electronic document (periodic/eventual) that gathers corporate and descriptive information required by the CVM: activities, risk factors, corporate and capital structure, management, compensation policies, information about securities, auditing, and other regulatory disclosures.",
        "FCA": "(Registration Form) an electronic form (periodic/eventual) with the company's official registration data and its updates: identification (CNPJ, corporate name), address, registration status, segment, identifier codes, and registration/contact information.",
        "DFP": "(Standardized Financial Statements) a periodic electronic form (related to the closed fiscal year) containing the standardized financial statements required by the CVM: Balance Sheet (BPA/BPP), Income Statement (DRE), Cash Flow Statement (DFC — direct/indirect methods, as applicable), Statement of Value Added (DVA), explanatory notes, independent auditor's report, and standardized annexes.",
        "ITR": "(Quarterly Information) a periodic electronic form with the statements and disclosures for each quarter — BPA/BPP, DRE, DFC (when applicable), and quarterly notes/disclosures required by the applicable regulation.",
        "IPE": "(Periodic and Eventual Documents) a set of unstructured documents (minutes, material facts, announcements, reports, prospectuses, official letters, etc.) made available with metadata and a link/file; the format and content vary depending on the document type.",
        "VLMO": "(Data on Negotiated and Held Securities) periodic reports on securities linked to the company (trades, quantities, positions, custody, and related information) provided as datasets on the CVM Open Data Portal.",
    }

    def get_available_docs(self) -> Dict[str, str]:
        """Gets a dictionary of all available documents."""
        return self.__DICT_AVAILABLE_DOCS.copy()

    def __get_available_docs_keys(self) -> List[str]:
        """Gets a list of available document codes."""
        return list(self.__DICT_AVAILABLE_DOCS.keys())

    def validate_docs_name(self, docs_name: str) -> None:
        """
        Validates that a document name is valid and of the correct type.

        Args:
            docs_name: The document name to validate.
        """
        if not isinstance(docs_name, str):
            raise InvalidTypeDoc(docs_name)

        key = docs_name.strip().upper()
        if key not in self.__get_available_docs_keys():
            raise InvalidDocName(docs_name, self.__get_available_docs_keys())


class UrlDocsCVM:
    """Generates URLs for CVM document downloads."""

    def __init__(self):
        """Initializes with the AvailableDocsCVM validator."""
        self.__available_docs = AvailableDocsCVM()

        self.__dict_url_docs = {
            "CGVN": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/CGVN/DADOS/cgvn_cia_aberta_",
            "FRE": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_",
            "FCA": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_",
            "DFP": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_",
            "ITR": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_",
            "IPE": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_",
            "VLMO": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_",
        }

    def get_url_docs(
        self, list_docs: Optional[List[str]] = None
    ) -> Tuple[Dict[str, str], Set[str]]:
        """
        Gets URLs for the specified documents or for all documents if none are specified.

        Args:
            list_docs: An optional list of document codes.

        Returns:
            A tuple containing a dictionary that maps document codes to their base URLs and a set of document codes.
        """
        if list_docs and not isinstance(list_docs, list):
            raise TypeError("list_docs must be a list of strings or None")

        dict_urls: Dict[str, str] = {}
        set_docs: set = set()

        if not list_docs:
            dict_urls = self.__dict_url_docs.copy()
            set_docs.update(self.__dict_url_docs.keys())
            return dict_urls, set_docs

        for doc in list_docs:
            self.__available_docs.validate_docs_name(doc)

            doc_key = doc.strip().upper()
            if doc_key not in self.__dict_url_docs:
                raise ValueError(f"No URL available for doc '{doc}'")

            if doc_key not in set_docs:
                dict_urls[doc_key] = self.__dict_url_docs[doc_key]
                set_docs.add(doc_key)

        return dict_urls, set_docs
