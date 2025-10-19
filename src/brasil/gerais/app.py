from Baixando_dados import *
from Concatenando_docs_antigos import *
from Criando_pastas import *
from Extraindo_arquivos import *
from funcoes import *
from url_e_nomes import *

ano_inicial = 2024
geral = False

ano_inicial, ano_final2, anos_dfp, anos_cgvn, anos_itr = (
    Instalar_Fundamentos_Empresas_BR(
        diretorio_cvm, diretorio_b3, ano_inicial, geral=geral
    )
)
extrair_arquivos_cvm(diretorio_cvm, anos_dfp, anos_cgvn, anos_itr)
concatenar_docs(diretorio_cvm, diretorio_b3, 2024, 2025, novos=True)
if geral:
    concatenar_docs(diretorio_cvm, diretorio_b3, 2010, 2023)
