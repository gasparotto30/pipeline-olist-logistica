"""Aplicação Streamlit do Dashboard Olist - Logística & Experiência.

Executável com: uv run streamlit run app.py
Segue estritamente a regra: a tela não calcula.
"""

from pathlib import Path
import streamlit as st
import painel

DB_FILE = Path("olist.duckdb")

MARTS_OBRIGATORIOS = [
    "kpis_logistica",
    "sla_mensal",
    "faixas_pontualidade_vs_nota",
    "logistica_por_uf",
    "gargalo_etapas",
    "ranking_sellers_logistica",
]

st.set_page_config(
    layout="wide",
    page_title="Olist · Logística & Experiência",
    page_icon="📦",
)


# 1. Tratamento de Erros e Validação de Banco
if not DB_FILE.exists():
    st.error(
        f"Arquivo do banco '{DB_FILE}' não encontrado.\n\n"
        "Execute o pipeline primeiro: `uv run python -m pipeline.marts`"
    )
    st.stop()


@st.cache_data
def carregar_dados(mtime: float) -> dict:
    """Lê todos os marts obrigatórios com invalidação automática se o banco for modificado."""
    return painel.ler(MARTS_OBRIGATORIOS)


try:
    dados = carregar_dados(DB_FILE.stat().st_mtime)
except Exception as e:
    st.error(
        f"Erro ao carregar marts necessários: {e}\n\n"
        "Execute novamente: `uv run python -m pipeline.marts`"
    )
    st.stop()

for mart in MARTS_OBRIGATORIOS:
    if mart not in dados or dados[mart].empty:
        st.error(
            f"Tabela marts.{mart} ausente ou vazia.\n\n"
            "Execute: `uv run python -m pipeline.marts`"
        )
        st.stop()

# 2. Cabeçalho & Controle de Período
col_titulo, col_filtro, col_btn = st.columns([5, 4, 1.5], vertical_alignment="center")

with col_titulo:
    st.title("📦 Olist · Logística & Experiência")
    st.caption("Torre de controle operacional de SLA, prazos e satisfação de entrega")

# Meses disponíveis para o slider
df_sla_completo = dados["sla_mensal"]
meses_disponiveis = df_sla_completo["ano_mes"].tolist()

with col_filtro:
    if len(meses_disponiveis) >= 2:
        mes_inicio_default = meses_disponiveis[0]
        mes_fim_default = meses_disponiveis[-1]
        
        # Seleciona de jan/2017 a ago/2018 se existirem
        if "2017-01" in meses_disponiveis:
            mes_inicio_default = "2017-01"
        if "2018-08" in meses_disponiveis:
            mes_fim_default = "2018-08"

        periodo_selecionado = st.select_slider(
            "Período de Análise:",
            options=meses_disponiveis,
            value=(mes_inicio_default, mes_fim_default),
            key="filtro_periodo",
        )
        st.caption("ℹ️ *Os cartões de KPI refletem a operação inteira (não recalculam no cliente).*")
    else:
        periodo_selecionado = (meses_disponiveis[0], meses_disponiveis[-1])

with col_btn:
    if st.button("🔄 Recarregar", help="Limpa o cache e recarrega os marts do banco"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# 3. Faixa 1 · Cartões Executivos (KPIs)
df_kpi = dados["kpis_logistica"]
row_kpi = df_kpi.iloc[0]

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.metric(
        label="SLA Cumprido",
        value=painel.pct(row_kpi["pct_no_prazo"]),
        help="Percentual de pedidos entregues até a data prevista",
    )
with c2:
    st.metric(
        label="Espera Média",
        value=painel.dias(row_kpi["dias_medio_entrega"]),
        help="Tempo médio entre a compra e a entrega ao cliente",
    )
with c3:
    st.metric(
        label="Antecipação Média",
        value=painel.dias(row_kpi["dias_medio_antecipacao"]),
        help="Dias de antecedência em relação ao prazo prometido",
    )
with c4:
    st.metric(
        label="Nota Média",
        value=painel.numero(row_kpi["nota_media"], casas=2),
        help="Média das avaliações dos pedidos entregues",
    )
with c5:
    st.metric(
        label="Notas Críticas (1-2★)",
        value=painel.pct(row_kpi["pct_nota_baixa"]),
        help="Percentual de pedidos que receberam nota 1 ou 2",
    )
with c6:
    st.metric(
        label="Entregas Totais",
        value=painel.numero(row_kpi["pedidos_entregues"]),
        help="Volume total de entregas no período",
    )

st.divider()

# 4. Faixa 2 · O SLA no Tempo (Largura Inteira)
# Aplica recorte de linhas puro, sem nenhum cálculo ou agregação
mes_ini, mes_fim = periodo_selecionado
df_sla_recortado = df_sla_completo[
    (df_sla_completo["ano_mes"] >= mes_ini) & (df_sla_completo["ano_mes"] <= mes_fim)
]
fig_tempo = painel.grafico_sla_mensal(df_sla_recortado)
st.plotly_chart(fig_tempo, width="stretch")

st.divider()

# 5. Faixa 3 · Correlação com Avaliações & Gargalo de Etapas (2 Colunas)
col_esq, col_dir = st.columns(2)

with col_esq:
    fig_nota = painel.grafico_faixas_nota(dados["faixas_pontualidade_vs_nota"])
    st.plotly_chart(fig_nota, width="stretch")

with col_dir:
    fig_etapas = painel.grafico_gargalo_etapas(dados["gargalo_etapas"])
    st.plotly_chart(fig_etapas, width="stretch")

st.divider()

# 6. Faixa 4 · SLA Geográfico e Performance de Sellers (2 Colunas)
col_geo, col_seller = st.columns(2)

with col_geo:
    fig_uf = painel.grafico_logistica_uf(dados["logistica_por_uf"], top_n=10)
    st.plotly_chart(fig_uf, width="stretch")

with col_seller:
    fig_seller = painel.grafico_sellers_prazo(dados["ranking_sellers_logistica"], top_n=10)
    st.plotly_chart(fig_seller, width="stretch")

