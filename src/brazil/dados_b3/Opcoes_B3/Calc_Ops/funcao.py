from docs.imports import *


def opcoes_calculo(
    preco_ativo_atual,
    preco_exercicio,
    tempo_ate_vencimento,
    taxa_livre_risco_anual,
    volatilidade,
    tipo_opcao,
):
    if tempo_ate_vencimento == 0:
        tempo_ate_vencimento = 1

    def calcular_preco_opcao(S, K, T, r, sigma, option):
        d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        if option == "Call":
            return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
        else:
            return K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)

    def norm_cdf(x):
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    try:
        # Parâmetros
        S = preco_ativo_atual
        K = preco_exercicio
        T = tempo_ate_vencimento / 252
        r = taxa_livre_risco_anual / 100
        sigma = volatilidade / 100
        option = tipo_opcao
        # Cálculo do preço da opção
        preco_opcao = calcular_preco_opcao(S, K, T, r, sigma, option=option)
        preco_opcao = round(preco_opcao, 2)
    except:
        preco_opcao = np.nan

    return preco_opcao


if __name__ == "__main__":
    import math

    import numpy as np

    preco_opcao = opcoes_calculo(
        preco_ativo_atual=29.95,
        preco_exercicio=41.07,
        tempo_ate_vencimento=22,
        taxa_livre_risco_anual=14.75,
        volatilidade=23.7,
        tipo_opcao="Put",
    )
