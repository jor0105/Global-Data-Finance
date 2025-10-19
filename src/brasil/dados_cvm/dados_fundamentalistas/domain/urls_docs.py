from dataclasses import dataclass


@dataclass
class UrlDocs:
    # CGVN - Informe do Código de Governança
    # Contém informações sobre práticas de governança corporativa adotadas
    # pela companhia (adesão a códigos, políticas, indicadores de governança).
    __URL_CGVN: str = (
        "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/CGVN/DADOS/cgvn_cia_aberta_"
    )

    # FRE - Formulário de Referência
    # Documento cadastral e descritivo amplo: atividades, estrutura societária,
    # administração, remuneração, auditoria, informações operacionais e outros
    # sub-arquivos CSV gerados a partir do formulário.
    __URL_FRE: str = (
        "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_"
    )

    # FCA - Formulário Cadastral
    # Dados cadastrais básicos e atualizações da companhia (CNPJ, razão social,
    # endereço, situação cadastral, segmento, código CVM, etc.).
    __URL_FCA: str = (
        "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_"
    )

    # DFP - Demonstrações Financeiras Padronizadas
    # Demonstrações financeiras anuais padronizadas (BP, DRE, DFC, MPA, notas),
    # disponibilizadas em formatos estruturados por período.
    __URL_DFP: str = (
        "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_"
    )

    # ITR - Informações Trimestrais
    # Demonstrações e notas trimestrais padronizadas (equivalente ao DFP, mas
    # para trimestres). Útil para séries temporais e análises intra-ano.
    __URL_ITR: str = (
        "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_"
    )

    # CAD Cias Abertas - Cadastro de companhias abertas (arquivo CSV)
    # Arquivo mestre com identificação das companhias: CNPJ, denominação,
    # código CVM, data de registro, situação, segmento, etc.
    __URL_CIAS_ABERTAS: str = (
        "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
    )

    # IPE - Documentos periódicos e eventuais não estruturados
    # Conjunto que inclui documentos em formato não totalmente estruturado
    # (atas, comunicados, laudos, relatórios) com metadados e links.
    __URL_IPE: str = (
        "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_"
    )

    # VLMO - Valores Mobiliários Negociados e Detidos
    # Informações sobre valores mobiliários negociados/detidos relacionados
    # à companhia: posições, quantidades e valores, usado para análises de mercado.
    __URL_VLMO: str = (
        "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_"
    )

    @classmethod
    def get(cls, key: str) -> str | None:
        """Retorna a URL correspondente à chave especificada.

        Chaves aceitas (case-insensitive): 'CGVN','FRE','FCA','DFP','ITR',
        'CAD_CIAS_ABERTAS' (ou 'CAD'), 'IPE', 'VLMO'. Retorna None se chave
        desconhecida.
        """
        mapping = {
            "CGVN": cls.__URL_CGVN,
            "FRE": cls.__URL_FRE,
            "FCA": cls.__URL_FCA,
            "DFP": cls.__URL_DFP,
            "ITR": cls.__URL_ITR,
            "CAD_CIAS_ABERTAS": cls.__URL_CIAS_ABERTAS,
            "CAD": cls.__URL_CIAS_ABERTAS,
            "IPE": cls.__URL_IPE,
            "VLMO": cls.__URL_VLMO,
        }
        return mapping.get(key.upper())
