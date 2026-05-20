"""Core domain for CVM fundamental_stocks_data.

Consolidates the prior `domain/` layer (available docs/years, URL builder,
download result) into a single module per the flat per-source layout.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

from .errors import (
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidTypeDoc,
)


class AvailableDocsCVM:
    """Manages information about available CVM document types."""

    __DICT_AVAILABLE_DOCS: Dict[str, str] = {
        'CGVN': '(Governance Code Report) a periodic document that records information about adherence/compatibility with the Corporate Governance Code for publicly traded companies — governance structure, committees, policies, and relevant indicators.',
        'FRE': '(Reference Form) an electronic document (periodic/eventual) that gathers corporate and descriptive information required by the CVM: activities, risk factors, corporate and capital structure, management, compensation policies, information about securities, auditing, and other regulatory disclosures.',
        'FCA': "(Registration Form) an electronic form (periodic/eventual) with the company's official registration data and its updates: identification (CNPJ, corporate name), address, registration status, segment, identifier codes, and registration/contact information.",
        'DFP': "(Standardized Financial Statements) a periodic electronic form (related to the closed fiscal year) containing the standardized financial statements required by the CVM: Balance Sheet (BPA/BPP), Income Statement (DRE), Cash Flow Statement (DFC — direct/indirect methods, as applicable), Statement of Value Added (DVA), explanatory notes, independent auditor's report, and standardized annexes.",
        'ITR': '(Quarterly Information) a periodic electronic form with the statements and disclosures for each quarter — BPA/BPP, DRE, DFC (when applicable), and quarterly notes/disclosures required by the applicable regulation.',
        'IPE': '(Periodic and Eventual Documents) a set of unstructured documents (minutes, material facts, announcements, reports, prospectuses, official letters, etc.) made available with metadata and a link/file; the format and content vary depending on the document type.',
        'VLMO': '(Data on Negotiated and Held Securities) periodic reports on securities linked to the company (trades, quantities, positions, custody, and related information) provided as datasets on the CVM Open Data Portal.',
    }

    def get_available_docs(self) -> Dict[str, str]:
        """Gets a dictionary of all available documents."""
        return self.__DICT_AVAILABLE_DOCS.copy()

    def __get_available_docs_keys(self) -> List[str]:
        """Gets a list of available document codes."""
        return list(self.__DICT_AVAILABLE_DOCS.keys())

    def validate_docs_name(self, docs_name: str) -> None:
        """Validate that a document name is valid and of the correct type."""
        if not isinstance(docs_name, str):
            raise InvalidTypeDoc(docs_name)

        key = docs_name.strip().upper()
        if key not in self.__get_available_docs_keys():
            raise InvalidDocName(docs_name, self.__get_available_docs_keys())


class UrlDocsCVM:
    """Generates URLs for CVM document downloads."""

    def __init__(self):
        self.__available_docs = AvailableDocsCVM()

        self.__dict_url_docs = {
            'CGVN': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/CGVN/DADOS/cgvn_cia_aberta_',
            'FRE': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_',
            'FCA': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_',
            'DFP': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_',
            'ITR': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_',
            'IPE': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_',
            'VLMO': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_',
        }

    def get_url_docs(
        self, list_docs: Optional[List[str]] = None
    ) -> Tuple[Dict[str, str], Set[str]]:
        """Get URLs for specified docs (or all docs if `list_docs` is None)."""
        if list_docs and not isinstance(list_docs, list):
            raise TypeError('list_docs must be a list of strings or None')

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


class AvailableYearsCVM:
    """Provides minimum allowed years and helpers for CVM documents."""

    __MIN_GENERAL_YEAR: int = 2010
    __MIN_ITR_YEAR: int = 2011
    __MIN_CGVN_VLMO_YEAR: int = 2018

    def get_current_year(self) -> int:
        """Return current year (system date)."""
        return date.today().year

    def get_minimal_general_year(self) -> int:
        """Return minimum supported year for general documents."""
        return self.__MIN_GENERAL_YEAR

    def get_minimal_itr_year(self) -> int:
        """Return minimum supported year for ITR documents."""
        return self.__MIN_ITR_YEAR

    def get_minimal_cgvn_vlmo_year(self) -> int:
        """Return minimum supported year for CGVN/VLMO documents."""
        return self.__MIN_CGVN_VLMO_YEAR

    def __validate_years(self, initial_year: int, last_year: int) -> None:
        if (
            not isinstance(initial_year, int)
            or initial_year < self.get_minimal_general_year()
            or initial_year > self.get_current_year()
        ):
            raise InvalidFirstYear(
                self.get_minimal_general_year(), self.get_current_year()
            )

        if (
            not isinstance(last_year, int)
            or last_year > self.get_current_year()
            or initial_year > last_year
        ):
            raise InvalidLastYear(initial_year, self.get_current_year())

    def return_range_years(
        self,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
    ) -> range:
        """Return inclusive year range; defaults span all supported years."""
        if initial_year is None:
            initial_year = self.get_minimal_general_year()
        if last_year is None:
            last_year = self.get_current_year()

        self.__validate_years(initial_year, last_year)

        return range(initial_year, last_year + 1)


class DictZipsToDownloadCVM:
    """Builds the per-doc ZIP-URL map for the requested year range."""

    def __init__(self):
        self._url_docs = UrlDocsCVM()
        self._available_years = AvailableYearsCVM()

    def get_dict_zips_to_download(
        self,
        list_docs: Optional[List[str]] = None,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
    ) -> Tuple[Dict[str, List[str]], Set[str]]:
        """Build a `{doc_code: [zip_url_per_year]}` map plus the doc set."""
        range_years: range = self._available_years.return_range_years(
            initial_year, last_year
        )

        dict_urls_docs, set_docs = self._url_docs.get_url_docs(list_docs)

        dict_zips_to_download: Dict[str, List[str]] = {
            doc: [url + str(year) + '.zip' for year in range_years]
            for doc, url in dict_urls_docs.items()
        }

        return dict_zips_to_download, set_docs


@dataclass
class DownloadResultCVM:
    """Aggregated result of a CVM download run."""

    successful_downloads: List[str] = field(default_factory=list)
    failed_downloads: Dict[str, str] = field(default_factory=dict)
    elapsed_time: float = 0.0

    @property
    def success_count_downloads(self) -> int:
        return len(self.successful_downloads)

    @property
    def error_count_downloads(self) -> int:
        return len(self.failed_downloads)

    def add_success_downloads(self, item: str) -> None:
        if item not in self.successful_downloads:
            self.successful_downloads.append(item)

    def add_error_downloads(self, item: str, error: str) -> None:
        self.failed_downloads[item] = error

    def __str__(self) -> str:
        return (
            f'DownloadResultCVM(success={self.success_count_downloads}, '
            f'errors={self.error_count_downloads})'
        )
