import time
from concurrent.futures import ThreadPoolExecutor

from .Capital_Social_B3_Acoes.funcao import dados_capital_social_br
from .common.io_utils import write_parquet
from .cotacao_mt5 import *  # noqa: F403
from .Dados_B3_Acoes.Funcao_Dados_B3.funcao import dados_acoes_b3
from .Dados_B3_Acoes.Percentual_ibov.funcao import percentual_ibov
from .docs.local_para_baixar import (
    acoes_ibov,
    dados_acoes_b3_doc,
    dividendos_status_invest_doc,
    indicadores_atuais_status_doc,
    opcoes_b3_doc,
)
from .Opcoes_B3.app_ops import dados_opcoes_b3
from .Status_Invest_Acoes.Dados_Atuais_Status.funcao import dados_status_atuais
from .Status_Invest_Acoes.Dados_Hist_Status.funcao1 import *  # noqa: F403
from .Status_Invest_Acoes.Dados_Hist_Status.funcao2 import *  # noqa: F403
from .Status_Invest_Acoes.Dados_Hist_Status.Hist_Unicos.baixar_cvm_status import (
    baixar_dados_isentos_cvm,
)
from .Status_Invest_Acoes.Divs_Status_Invest.funcao import divs_status_invest

taxa_selic_atual = 15

##### CÓDIGO AÇÕES B3 #####

with ThreadPoolExecutor(max_workers=4) as ex:
    futures = {
        'ibov': ex.submit(percentual_ibov),
        'acoes': ex.submit(dados_acoes_b3),
        'capsocial': ex.submit(dados_capital_social_br),
    }
    df_percentual_ibov = futures['ibov'].result()
    df_dados_acoes_b3 = futures['acoes'].result()
    df_cap_social = futures['capsocial'].result()
# Cria um mapeamento dos valores de capital social
mapping_ON = df_cap_social.set_index('Código')['ON'].to_dict()
mapping_PN = df_cap_social.set_index('Código')['PN'].to_dict()
mapping_Total = df_cap_social.set_index('Código')['Total'].to_dict()

# Usa o método map para criar as colunas
df_dados_acoes_b3['Quantidade de ações ON'] = (
    df_dados_acoes_b3['issuingCompany'].map(mapping_ON).fillna(0)
)
df_dados_acoes_b3['Quantidade de ações PN'] = (
    df_dados_acoes_b3['issuingCompany'].map(mapping_PN).fillna(0)
)
df_dados_acoes_b3['Quantidade de ações Totais'] = (
    df_dados_acoes_b3['issuingCompany'].map(mapping_Total).fillna(0)
)

df_dados_acoes_b3 = df_dados_acoes_b3[
    df_dados_acoes_b3['Quantidade de ações Totais'] > 10
]
write_parquet(df_dados_acoes_b3, dados_acoes_b3_doc)
print('Download Dados Ações B3 Concluído')
df_percentual_ibov = df_percentual_ibov.drop('Segmento', axis=True)
write_parquet(df_percentual_ibov.drop('Segmento', axis=True), acoes_ibov)
print('Download Porcentagem IBOV Concluído')


##### CÓDIGO OPÇÕES B3 ##### ## DIÁRIO ##
df_opcoes_b3 = dados_opcoes_b3(taxa_selic_atual)

# lista_opcoes = df_opcoes_b3[df_opcoes_b3['Posições Totais'].notna()]['Opção'].unique().tolist()
# df_opcoes_MT5 = atualizar_preco_mt5(lista_opcoes)


write_parquet(df_opcoes_b3, opcoes_b3_doc)
print('Download Dados Opções B3')
time.sleep(0.5)

# df_opcoes_b3_3 = dados_ajustes_divs()

##### CÓDIGO STATUS INVEST #####

df_indicadores_status_atuais = dados_status_atuais()  # DIÁRIO
write_parquet(df_indicadores_status_atuais, indicadores_atuais_status_doc)
print('Download Dados Atuais Indicadores Status Invest Concluído')
time.sleep(0.5)

# df_dados_hist_status_acao2 = dados_hist_status_acao2(df_indicadores_status_atuais)
# df_dados_hist_status_acao2.to_parquet(hist_indicadores_acoes_b3_doc)
# print('Download Dados Histórico Indicadores Status Invest Concluído')
# time.sleep(0.5)

df_divs_status_invest = divs_status_invest()
write_parquet(df_divs_status_invest, dividendos_status_invest_doc)
print('Download Dados Dividendos Status Invest Concluído')


resposta = input('Rodar código de ações que não estão na CVM? (s/Sim)')
if resposta.lower() in ['s', 'sim']:
    ano_inicial = 2024
    ano_final = 2025
    # ÚLTIMA INSTALAÇÃO DE AÇÕES QUE NÃO ESTÃO NA CVM #
    print('Iniciando instalações de empresas que não estão presentes na CVM')
    baixar_dados_isentos_cvm(ano_inicial, ano_final)
