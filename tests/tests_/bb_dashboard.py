import numpy as np  # Para cálculos numéricos
import pandas as pd
import plotly.express as px
import streamlit as st

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Dashboard Sanepar - Análise DRE")

# --- Título e Cabeçalho ---
st.title("Dashboard de Análise Sênior - Sanepar (SAPR)")
st.subheader("Foco: Demonstração do Resultado (DRE) - Dados do DFP")
st.caption(
    "Fonte: /home/jordan/Downloads/Docs_Cvm/DFP/2024/dfp_cia_aberta_DRE_ind_2024.parquet"
)


# --- Carregamento e Preparação dos Dados ---
@st.cache_data  # Usar cache para não recarregar a cada interação
def load_data(file_path):
    try:
        df = pd.read_parquet(file_path)
        # Filtrar por Sanepar (Ajuste o nome/CNPJ se necessário)
        # O CNPJ da Sanepar é 76.484.013/0001-45
        sanepar_cnpj = "76.484.013/0001-45"
        df_sanepar = df[df["CNPJ_CIA"] == sanepar_cnpj].copy()

        if df_sanepar.empty:
            st.error(f"Nenhum dado encontrado para o CNPJ {sanepar_cnpj} no arquivo.")
            return None, None

        # Converter colunas de data
        df_sanepar["DT_REFER"] = pd.to_datetime(df_sanepar["DT_REFER"])
        df_sanepar["DT_FIM_EXERC"] = pd.to_datetime(df_sanepar["DT_FIM_EXERC"])
        df_sanepar["DT_INI_EXERC"] = pd.to_datetime(df_sanepar["DT_INI_EXERC"])

        # Extrair Ano e Trimestre (baseado na data final do exercício)
        # Assume que o arquivo contém dados trimestrais ou anuais
        df_sanepar["ANO"] = df_sanepar["DT_FIM_EXERC"].dt.year
        df_sanepar["MES_FIM"] = df_sanepar["DT_FIM_EXERC"].dt.month

        # Identificar o período (Anual ou Trimestral - T1, T2, T3, T4)
        # Simples heurística: se mês for 12 e duração ~1 ano -> Anual, senão Trimestral
        df_sanepar["DURACAO_DIAS"] = (
            df_sanepar["DT_FIM_EXERC"] - df_sanepar["DT_INI_EXERC"]
        ).dt.days
        df_sanepar["PERIODO_TIPO"] = np.where(
            (df_sanepar["MES_FIM"] == 12) & (df_sanepar["DURACAO_DIAS"] > 350),
            "Anual",
            "Trimestral",  # Simplificação, pode precisar de ajuste
        )

        # Criar uma coluna de período legível (ex: 2024-T1, 2023-Anual)
        def get_quarter(month):
            if month <= 3:
                return "T1"
            elif month <= 6:
                return "T2"
            elif month <= 9:
                return "T3"
            else:
                return "T4"

        df_sanepar["PERIODO_LABEL"] = df_sanepar.apply(
            lambda row: (
                f"{row['ANO']}-Anual"
                if row["PERIODO_TIPO"] == "Anual"
                else f"{row['ANO']}-{get_quarter(row['MES_FIM'])}"
            ),
            axis=1,
        )

        # Ordenar os dados por período para gráficos
        df_sanepar = df_sanepar.sort_values(by="DT_FIM_EXERC")

        # Pivotar para análise de contas ao longo do tempo
        df_pivot = df_sanepar.pivot_table(
            index="PERIODO_LABEL",
            columns=["CD_CONTA", "DS_CONTA"],
            values="VL_CONTA",
            aggfunc="first",  # Assume um valor por conta/período
        )

        # Simplificar MultiIndex das colunas
        if isinstance(df_pivot.columns, pd.MultiIndex):
            df_pivot.columns = [f"{col[0]} | {col[1]}" for col in df_pivot.columns]

        return df_sanepar, df_pivot

    except FileNotFoundError:
        st.error(
            f"Erro: Arquivo Parquet não encontrado no caminho especificado: {file_path}"
        )
        return None, None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar o arquivo Parquet: {e}")
        return None, None


# --- Interface ---
# (Assume que o arquivo está na mesma pasta do script ou forneça o caminho completo)
file_path = (
    "/home/jordan/Downloads/Docs_Cvm/DFP/2024/dfp_cia_aberta_DRE_ind_2024.parquet"
)
df_raw, df_pivot = load_data(file_path)

if df_raw is not None and df_pivot is not None and not df_pivot.empty:
    st.sidebar.header("Filtros e Opções")
    # Seleção de Períodos (se houver mais de um)
    available_periods = df_pivot.index.unique().tolist()
    if len(available_periods) > 1:
        selected_period = st.sidebar.select_slider(
            "Selecione o Período para Destaques:",
            options=available_periods,
            value=available_periods[-1],  # Padrão: último período
        )
    else:
        selected_period = available_periods[0]

    # Mapeamento Básico de Contas Principais da DRE (Ajuste os códigos conforme seu arquivo DFP)
    # Estes são códigos comuns, mas VERIFIQUE no seu arquivo Parquet os códigos corretos para Sanepar
    conta_receita_liquida = "3.01"  # Receita de Venda de Bens e/ou Serviços (pode precisar somar ou ajustar)
    conta_custo = "3.02"  # Custo dos Bens e/ou Serviços Vendidos
    conta_lucro_bruto = "3.03"  # Lucro Bruto
    conta_desp_oper = "3.04"  # Despesas/Receitas Operacionais (Total)
    conta_desp_vendas = (
        "3.04.01"  # Despesas com Vendas (Exemplo, verificar código exato)
    )
    conta_desp_adm = "3.04.02"  # Despesas Gerais e Administrativas (Exemplo)
    conta_outras_rec_desp_op = "3.04.04"  # Outras Receitas Operacionais / Outras Despesas Operacionais (Exemplo)
    conta_resultado_fin = "3.07"  # Resultado Financeiro (Pode estar em outro nível)
    conta_lucro_antes_ir = (
        "3.09"  # Lucro Antes do Imposto de Renda e Contribuição Social
    )
    conta_ir_csll = "3.10"  # Imposto de Renda e Contribuição Social sobre o Lucro
    conta_lucro_liquido = "3.11"  # Lucro Líquido do Exercício

    # --- Funções Auxiliares para buscar valores ---
    def get_value(df_piv, period, conta_prefix):
        cols = [col for col in df_piv.columns if col.startswith(conta_prefix + " |")]
        if cols:
            val = df_piv.loc[period, cols[0]]
            return val if pd.notna(val) else 0
        return 0

    def get_account_name(df_piv, conta_prefix):
        cols = [col for col in df_piv.columns if col.startswith(conta_prefix + " |")]
        if cols:
            return cols[0].split(" | ")[1]
        return f"Conta {conta_prefix} (Não encontrada)"

    # --- Extrair Dados do Período Selecionado ---
    receita_liq = get_value(df_pivot, selected_period, conta_receita_liquida)
    custo = abs(
        get_value(df_pivot, selected_period, conta_custo)
    )  # Geralmente negativo
    lucro_bruto = get_value(
        df_pivot, selected_period, conta_lucro_bruto
    )  # Pode ser calculado: receita - custo
    # Se lucro bruto não existir diretamente, calcula
    if lucro_bruto == 0 and receita_liq != 0:
        lucro_bruto = receita_liq - custo

    desp_oper_total = abs(
        get_value(df_pivot, selected_period, conta_desp_oper)
    )  # Agregado, verificar se faz sentido
    desp_vendas = abs(get_value(df_pivot, selected_period, conta_desp_vendas))
    desp_adm = abs(get_value(df_pivot, selected_period, conta_desp_adm))
    outras_rec_desp_op_val = get_value(
        df_pivot, selected_period, conta_outras_rec_desp_op
    )  # Pode ser positivo ou negativo

    # Tentar calcular Lucro Operacional (EBIT) = Lucro Bruto - Desp Vendas - Desp Adm +/- Outras Rec/Desp Op
    # Nem sempre o DFP tem uma linha direta de EBIT clara
    ebit_calculado = lucro_bruto - desp_vendas - desp_adm + outras_rec_desp_op_val

    resultado_fin = get_value(df_pivot, selected_period, conta_resultado_fin)
    lucro_antes_ir = get_value(df_pivot, selected_period, conta_lucro_antes_ir)
    ir_csll = abs(
        get_value(df_pivot, selected_period, conta_ir_csll)
    )  # Geralmente negativo
    lucro_liquido = get_value(df_pivot, selected_period, conta_lucro_liquido)

    # Calcular Margens
    margem_bruta = (lucro_bruto / receita_liq * 100) if receita_liq else 0
    margem_ebit_calc = (ebit_calculado / receita_liq * 100) if receita_liq else 0
    margem_liquida = (lucro_liquido / receita_liq * 100) if receita_liq else 0

    # --- Dashboard Layout ---
    st.header(f"Análise do Período: {selected_period}")

    # Métricas Principais
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Receita Líquida",
        f"R$ {receita_liq/1e6:.2f} M",
        help=get_account_name(df_pivot, conta_receita_liquida),
    )
    col2.metric(
        "Lucro Bruto",
        f"R$ {lucro_bruto/1e6:.2f} M",
        f"{margem_bruta:.1f}% Margem",
        help=get_account_name(df_pivot, conta_lucro_bruto),
    )
    col3.metric(
        "EBIT (Calculado)",
        f"R$ {ebit_calculado/1e6:.2f} M",
        f"{margem_ebit_calc:.1f}% Margem",
        help="Lucro Bruto - Desp. Vendas - Desp. Adm +/- Outras Rec/Desp Op.",
    )
    col4.metric(
        "Lucro Líquido",
        f"R$ {lucro_liquido/1e6:.2f} M",
        f"{margem_liquida:.1f}% Margem",
        help=get_account_name(df_pivot, conta_lucro_liquido),
    )

    st.divider()

    # Gráficos de Tendência
    st.header("Tendências Temporais (DRE)")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Receita Líquida e Lucro Líquido")
        try:
            df_plot_lucro = pd.DataFrame(
                {
                    "Receita Líquida": df_pivot[
                        get_account_name(df_pivot, conta_receita_liquida)
                    ],
                    "Lucro Líquido": df_pivot[
                        get_account_name(df_pivot, conta_lucro_liquido)
                    ],
                }
            ).reset_index()

            fig_lucro = px.line(
                df_plot_lucro,
                x="PERIODO_LABEL",
                y=["Receita Líquida", "Lucro Líquido"],
                title="Evolução da Receita e Lucro Líquido",
                markers=True,
                labels={"value": "Valor (R$)", "PERIODO_LABEL": "Período"},
            )
            fig_lucro.update_layout(
                yaxis_title="Valor (R$)", xaxis_title="Período", hovermode="x unified"
            )
            st.plotly_chart(fig_lucro, use_container_width=True)
        except Exception as e:
            st.warning(
                f"Não foi possível gerar o gráfico de Receita/Lucro: Verifique os códigos das contas. Erro: {e}"
            )

    with col_g2:
        st.subheader("Margens (%)")
        try:
            # Recalcular margens para todos os períodos
            df_pivot["Margem Bruta (%)"] = (
                df_pivot[get_account_name(df_pivot, conta_lucro_bruto)]
                / df_pivot[get_account_name(df_pivot, conta_receita_liquida)]
            ) * 100
            # Recalculo do EBIT para todos os períodos
            df_pivot["EBIT Calculado"] = (
                df_pivot[get_account_name(df_pivot, conta_lucro_bruto)]
                - abs(
                    df_pivot.get(get_account_name(df_pivot, conta_desp_vendas), 0)
                )  # abs() e get() para segurança
                - abs(df_pivot.get(get_account_name(df_pivot, conta_desp_adm), 0))
                + df_pivot.get(get_account_name(df_pivot, conta_outras_rec_desp_op), 0)
            )

            df_pivot["Margem EBIT Calc (%)"] = (
                df_pivot["EBIT Calculado"]
                / df_pivot[get_account_name(df_pivot, conta_receita_liquida)]
            ) * 100
            df_pivot["Margem Líquida (%)"] = (
                df_pivot[get_account_name(df_pivot, conta_lucro_liquido)]
                / df_pivot[get_account_name(df_pivot, conta_receita_liquida)]
            ) * 100

            df_plot_margens = df_pivot[
                ["Margem Bruta (%)", "Margem EBIT Calc (%)", "Margem Líquida (%)"]
            ].reset_index()

            fig_margens = px.line(
                df_plot_margens,
                x="PERIODO_LABEL",
                y=["Margem Bruta (%)", "Margem EBIT Calc (%)", "Margem Líquida (%)"],
                title="Evolução das Margens",
                markers=True,
                labels={"value": "Margem (%)", "PERIODO_LABEL": "Período"},
            )
            fig_margens.update_layout(
                yaxis_title="Margem (%)", xaxis_title="Período", hovermode="x unified"
            )
            st.plotly_chart(fig_margens, use_container_width=True)
        except Exception as e:
            st.warning(
                f"Não foi possível gerar o gráfico de Margens: Verifique os códigos das contas. Erro: {e}"
            )

    st.divider()

    # Tabela DRE Simplificada e Análise
    st.header("Demonstração do Resultado (Simplificada)")

    dre_simplificada = {
        "Conta": [
            get_account_name(df_pivot, conta_receita_liquida),
            get_account_name(df_pivot, conta_custo),
            f"**{get_account_name(df_pivot, conta_lucro_bruto)}**",
            get_account_name(df_pivot, conta_desp_vendas),
            get_account_name(df_pivot, conta_desp_adm),
            get_account_name(df_pivot, conta_outras_rec_desp_op),
            "**EBIT (Calculado)**",
            get_account_name(df_pivot, conta_resultado_fin),
            f"**{get_account_name(df_pivot, conta_lucro_antes_ir)}**",
            get_account_name(df_pivot, conta_ir_csll),
            f"**{get_account_name(df_pivot, conta_lucro_liquido)}**",
        ],
        selected_period: [
            receita_liq,
            -custo,
            lucro_bruto,
            -desp_vendas,
            -desp_adm,
            outras_rec_desp_op_val,
            ebit_calculado,
            resultado_fin,
            lucro_antes_ir,
            -ir_csll,
            lucro_liquido,
        ],
    }
    df_dre_display = pd.DataFrame(dre_simplificada)

    # Adicionar % da Receita Líquida
    df_dre_display[f"% Receita ({selected_period})"] = df_dre_display[
        selected_period
    ].apply(
        lambda x: (
            f"{(x / receita_liq * 100):.1f}%" if receita_liq and pd.notna(x) else "N/A"
        )
    )

    st.dataframe(
        df_dre_display.style.format(
            {
                selected_period: "{:,.0f}",
            }
        ),
        use_container_width=True,
    )

    # Análise Sênior (Textual)
    st.subheader("📝 Análise do Analista Sênior (Baseado na DRE)")
    st.markdown(
        f"""
    **Período Analisado:** {selected_period}

    * **Receita:** A Receita Líquida atingiu R$ {receita_liq/1e6:,.2f} M. _[Comparar com períodos anteriores ou guidance da empresa, se disponíveis nos dados, para avaliar crescimento]._
    * **Rentabilidade Bruta:** A Margem Bruta ficou em {margem_bruta:.1f}%. _[Analisar a tendência dessa margem. Estabilidade ou crescimento é positivo. Quedas podem indicar pressão nos custos ou preços]._ Custo dos Serviços Vendidos representou {(custo / receita_liq * 100) if receita_liq else 0:.1f}% da receita.
    * **Despesas Operacionais:** Despesas com Vendas ({(desp_vendas / receita_liq * 100) if receita_liq else 0:.1f}%) e Administrativas ({(desp_adm / receita_liq * 100) if receita_liq else 0:.1f}%) totalizaram R$ {(desp_vendas + desp_adm)/1e6:,.2f} M. _[Observar a evolução dessas despesas em relação à receita (diluição operacional). Controle de despesas é crucial, especialmente em setores regulados como saneamento]._ O item 'Outras Receitas/Despesas Operacionais' teve um impacto de R$ {outras_rec_desp_op_val/1e6:,.2f} M. _[Investigar a natureza dessas outras receitas/despesas, se recorrentes ou não]._
    * **Rentabilidade Operacional:** O EBIT (calculado) foi de R$ {ebit_calculado/1e6:,.2f} M, com margem de {margem_ebit_calc:.1f}%. _[Analisar a tendência da margem EBIT. É um indicador chave da eficiência operacional core da empresa]._
    * **Resultado Financeiro:** O resultado financeiro foi de R$ {resultado_fin/1e6:,.2f} M ({(resultado_fin / receita_liq * 100) if receita_liq else 0:.1f}% da receita). _[Importante em empresas de capital intensivo como saneamento. Negativo indica despesas de juros maiores que receitas financeiras. Monitorar o impacto do endividamento e taxas de juros]._
    * **Lucratividade Líquida:** O Lucro Líquido alcançou R$ {lucro_liquido/1e6:,.2f} M, com Margem Líquida de {margem_liquida:.1f}%. A alíquota efetiva de IR/CSLL foi de {(ir_csll / lucro_antes_ir * 100) if lucro_antes_ir else 0:.1f}%. _[Analisar a tendência do lucro e margem líquida. Verificar fatores não recorrentes que possam ter impactado o resultado]._

    **Pontos de Atenção (Geral):**
    * **Regulação:** O setor de saneamento é altamente regulado. Mudanças tarifárias e regras de investimento impactam diretamente os resultados. (Não visível apenas na DRE).
    * **Endividamento:** Empresas de saneamento costumam ter alto endividamento devido aos investimentos. O custo dessa dívida (resultado financeiro) é crucial. (Necessita Balanço Patrimonial).
    * **Investimentos (CAPEX):** O nível de investimento impacta a base de ativos remunerada e o crescimento futuro, mas não é diretamente visto na DRE (Necessita Fluxo de Caixa/Notas).
    * **Eficiência Operacional:** Controle de custos e despesas (Pessoal, Materiais, Serviços de Terceiros - PMSO) é vital para a rentabilidade.
    * **Comparação:** Comparar esses números com períodos anteriores, com o guidance da empresa e com empresas pares do setor é essencial para uma análise completa.

    **Disclaimer:** Esta análise é estritamente baseada nos dados da Demonstração do Resultado extraídos do arquivo Parquet fornecido e pode não refletir a totalidade da situação financeira ou operacional da Sanepar. Códigos de conta podem precisar de validação cruzada com o plano de contas oficial da CVM/B3.
    """
    )

    # Mostrar Dados Brutos Filtrados (Opcional)
    with st.expander("Ver Dados Brutos Filtrados da Sanepar (DRE)"):
        st.dataframe(
            df_raw[df_raw["GRUPO_DFP"].str.contains("DRE", na=False)],
            use_container_width=True,
        )

    with st.expander("Ver Tabela Pivotada Completa"):
        st.dataframe(
            df_pivot.style.format("{:,.0f}", na_rep="-"), use_container_width=True
        )


else:
    st.warning(
        "Não foi possível carregar ou processar os dados da Sanepar do arquivo Parquet fornecido."
    )
