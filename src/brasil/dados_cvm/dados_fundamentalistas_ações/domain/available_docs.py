from typing import Dict, List, Optional

from ..exceptions.exceptions import InvalidDocName, InvalidTypeDoc


class AvailableDocs:
    __DICT_AVAILABLE_DOCS: Dict[str, str] = {
        "CGVN": "(Informe do Código de Governança) informações sobre práticas de governança corporativa adotadas pela companhia, políticas e indicadores.",
        "FRE": "(Formulário de Referência) documento cadastral e descritivo amplo sobre a companhia (atividades, estrutura, administração, remuneração, auditoria).",
        "FCA": "(Formulário Cadastral) dados cadastrais básicos e atualizações da companhia (CNPJ, razão social, endereço, situação cadastral, segmento, código CVM).",
        "DFP": "(Demonstrações Financeiras Padronizadas) demonstrações financeiras anuais padronizadas (BP, DRE, DFC, MPA, notas).",
        "ITR": "(Informações Trimestrais) demonstrações e notas trimestrais padronizadas para análises intra-ano.",
        "IPE": "(Documentos periódicos e eventuais) documentos não totalmente estruturados como atas, comunicados, laudos e relatórios, com metadados e links.",
        "VLMO": "(Valores Mobiliários) informações sobre valores mobiliários negociados e detidos relacionados à companhia (posições, quantidades e valores).",
    }

    def get_available_docs(self) -> Dict[str, str]:
        return self.__DICT_AVAILABLE_DOCS.copy()

    def __get_available_docs_keys(self) -> List[str]:
        return list(self.__DICT_AVAILABLE_DOCS.keys())

    def validate_docs_name(self, docs_name: str) -> None:
        if not isinstance(docs_name, str):
            raise InvalidTypeDoc(docs_name)

        key = docs_name.strip().upper()
        if key not in self.__get_available_docs_keys():
            raise InvalidDocName(docs_name, self.__get_available_docs_keys())


class UrlDocs:
    def __init__(self):
        self._available_docs = AvailableDocs()

    __DICT_URL_DOCS: Dict[str, str] = {
        "CGVN": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/CGVN/DADOS/cgvn_cia_aberta_",
        "FRE": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_",
        "FCA": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_",
        "DFP": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_",
        "ITR": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_",
        "IPE": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_",
        "VLMO": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_",
    }

    def get_url_docs(self, list_docs: Optional[List[str]] = None) -> List[str]:
        if list_docs and not isinstance(list_docs, list):
            raise TypeError("List_docs must be a built-in list of strings or None")

        list_urls: List[str] = []
        seen_docs: set = set()

        if not list_docs:
            for _, item in self.__DICT_URL_DOCS.items():
                list_urls.append(item)
            return list_urls

        for doc in list_docs:
            self._available_docs.validate_docs_name(doc)

            doc_key = doc.upper()
            if doc_key not in self.__DICT_URL_DOCS:
                raise ValueError(f"No URL available for doc '{doc}'")

            if doc_key not in seen_docs:
                list_urls.append(self.__DICT_URL_DOCS[doc_key])
                seen_docs.add(doc_key)

        return list_urls
