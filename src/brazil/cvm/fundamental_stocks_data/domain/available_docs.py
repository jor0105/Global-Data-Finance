from typing import Dict, List, Optional, Set, Tuple

from ..exceptions import InvalidDocName, InvalidTypeDoc


class AvailableDocs:
    """Manages information about available CVM document types.

    This class maintains a registry of valid CVM document codes and provides
    validation and retrieval methods.

    Attributes:
        __DICT_AVAILABLE_DOCS: Private dictionary mapping document codes to descriptions.
    """

    __DICT_AVAILABLE_DOCS: Dict[str, str] = {
        "CGVN": "(Informe do Código de Governança) documento periódico que registra informações sobre adesão/compatibilidade às práticas do Código de Governança de Companhias Abertas — estrutura de governança, comitês, políticas e indicadores relevantes.",
        "FRE": "(Formulário de Referência) documento eletrônico (periódico/eventual) que reúne informações cadastrais e descritivas exigidas pela CVM: atividades, fatores de risco, estrutura societária e de capital, administração, políticas de remuneração, informações sobre valores mobiliários, auditoria e demais divulgações regulatórias.",
        "FCA": "(Formulário Cadastral) formulário eletrônico (periódico/eventual) com os dados cadastrais oficiais da companhia e suas atualizações: identificação (CNPJ, razão social), endereço, situação cadastral, segmento, códigos identificadores e informações de registro/contato.",
        "DFP": "(Demonstrações Financeiras Padronizadas) formulário eletrônico periódico (relativo ao exercício social encerrado) com as demonstrações financeiras padronizadas exigidas pela CVM: Balanço Patrimonial (BPA/BPP), Demonstração do Resultado (DRE), Demonstração dos Fluxos de Caixa (DFC — métodos direto/indireto conforme aplicável), Demonstração do Valor Adicionado (DVA), notas explicativas, relatório do auditor independente e anexos padronizados.",
        "ITR": "(Informações Trimestrais) formulário eletrônico periódico com as demonstrações e divulgações relativas a cada trimestre — BPA/BPP, DRE, DFC (quando aplicável), e notas/divulgações trimestrais exigidas pela regulamentação aplicável.",
        "IPE": "(Periódicos e Eventuais) conjunto de documentos não-estruturados (atas, fatos relevantes, comunicados, laudos, prospectos, ofícios etc.) disponibilizados com metadados e link/arquivo; formato e conteúdo variam conforme o tipo de documento.",
        "VLMO": "(Valores Mobiliários Negociados e Detidos) informes periódicos sobre valores mobiliários vinculados à companhia (operações, quantidades, posições, custódia e informações correlatas) disponibilizados como conjunto de dados no Portal Dados Abertos da CVM.",
    }

    def get_available_docs(self) -> Dict[str, str]:
        """Get dictionary of all available documents.

        Returns:
            Dictionary mapping document codes to their descriptions.
            Returns a copy to prevent external modification.
        """
        return self.__DICT_AVAILABLE_DOCS.copy()

    def __get_available_docs_keys(self) -> List[str]:
        """Get list of available document codes.

        Returns:
            List of valid document codes.
        """
        return list(self.__DICT_AVAILABLE_DOCS.keys())

    def validate_docs_name(self, docs_name: str) -> None:
        """Validate that a document name is valid and of correct type.

        Args:
            docs_name: Document name to validate.

        Raises:
            InvalidTypeDoc: If docs_name is not a string.
            InvalidDocName: If docs_name is not in the list of valid documents.
        """
        if not isinstance(docs_name, str):
            raise InvalidTypeDoc(docs_name)

        key = docs_name.strip().upper()
        if key not in self.__get_available_docs_keys():
            raise InvalidDocName(docs_name, self.__get_available_docs_keys())


class UrlDocs:
    """Generates URLs for CVM document downloads.

    This class maintains URLs for each document type and provides methods
    to retrieve them based on document selection.

    Attributes:
        _available_docs: Instance of AvailableDocs for validation.
        __dict_url_docs: Private dictionary mapping documents to base URLs.
    """

    def __init__(self):
        """Initialize with AvailableDocs validator."""
        self.__available_docs = AvailableDocs()

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
        """Get URLs for specified documents or all documents if none specified.

        Args:
            list_docs: Optional list of document codes. If None or empty, returns URLs for all documents.

        Returns:
            Dictionary mapping document codes to their base URLs.

        Raises:
            TypeError: If list_docs is not a list or None.
            InvalidDocName: If any document code in list_docs is invalid.
            InvalidTypeDoc: If any element in list_docs is not a string.
        """
        if list_docs and not isinstance(list_docs, list):
            raise TypeError("List_docs must be a built-in list of strings or None")

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
