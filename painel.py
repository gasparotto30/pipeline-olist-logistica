"""SPEC DO PAINEL · ARQUITETURA E MOTIVOS DAS REGRAS

1. LEITURA:
   - ler(marts) -> dict[str, pd.DataFrame].
   - Cada tabela lê estritamente 'SELECT * FROM marts.<nome>'.
   - Conexão efêmera com duckdb.connect(db_path, read_only=True), aberta e fechada dentro de ler().
   - MOTIVO: Evitar travamento (file lock) no DuckDB enquanto o dashboard estiver em execução, permitindo
     que o pipeline de atualização execute em paralelo.

2. NENHUM CÁLCULO NO FRONTEND:
   - PROIBIDO em painel.py e app.py: operacoes de agregacao analitica (agrupamentos, somas, medias, fusoes de tabelas) e contas aritmeticas entre colunas.
   - PERMITIDO: filtros de linhas, ordenação, slice/head, renomear colunas e formatação textual.
   - MOTIVO: Princípio de Separação de Responsabilidades. Toda regra de negócio e agregação pertence à camada
     analítica (Marts SQL), garantindo reprodutibilidade, governança e testes unitários no banco.

3. FORMATAÇÃO DETERMINÍSTICA:
   - Funções puras sem dependência de locale do sistema operacional.
   - Ponto como separador de milhar e vírgula como separador decimal.
   - MOTIVO: O formato exibido deve ser consistente independente da máquina ou SO em que a aplicação rodar.

4. FIGURAS PURAS REUTILIZÁVEIS:
   - Gráficos gerados com plotly.express e desacoplados do Streamlit.
   - MOTIVO: Permite reaproveitamento idêntico tanto na aplicação interativa (app.py) quanto no relatório
     HTML congelado (relatorio.py).
"""

from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pipeline.db import DB_PATH


def ler(marts: list[str], db_path: Path | str = DB_PATH) -> dict[str, pd.DataFrame]:
    """Lê as tabelas especificadas do schema marts.* em modo somente leitura."""
    tabelas: dict[str, pd.DataFrame] = {}
    path_str = str(db_path)
    
    # Abre e fecha pontualmente para não reter lock
    with duckdb.connect(path_str, read_only=True) as con:
        for nome in marts:
            tabelas[nome] = con.execute(f"SELECT * FROM marts.{nome};").df()
            
    return tabelas


def numero(valor: float | int | None, casas: int = 0) -> str:
    """Formata número com ponto para milhar e vírgula para decimal."""
    if valor is None or pd.isna(valor):
        return "-"
    if casas == 0:
        inteiro = int(round(valor))
        return f"{inteiro:,}".replace(",", ".")
    formatado = f"{valor:,.{casas}f}"
    # Troca temporária para inverter vírgula e ponto
    return formatado.replace(".", "X").replace(",", ".").replace("X", ",")


def reais(valor: float | int | None, casas: int = 2) -> str:
    """Formata valor monetário no padrão R$ 1.234,56."""
    if valor is None or pd.isna(valor):
        return "-"
    return f"R$ {numero(valor, casas=casas)}"


def pct(valor: float | int | None, casas: int = 1) -> str:
    """Formata percentual no padrão 93,2%."""
    if valor is None or pd.isna(valor):
        return "-"
    return f"{numero(valor, casas=casas)}%"


def dias(valor: float | int | None, casas: int = 1) -> str:
    """Formata duração em dias."""
    if valor is None or pd.isna(valor):
        return "-"
    return f"{numero(valor, casas=casas)} dias"


# --- Funções puras de geração dos gráficos (Plotly) ---

PALETA_AZUL = "#1E3A8A"
PALETA_DESTAQUE = "#DC2626"
PALETA_VERDE = "#059669"


def grafico_sla_mensal(df: pd.DataFrame) -> go.Figure:
    """Gráfico de linha com marcadores: % SLA cumprido ao longo dos meses."""
    fig = px.line(
        df,
        x="ano_mes",
        y="pct_no_prazo",
        markers=True,
        title="02 · Cumprimento de SLA no Tempo (% Entregas no Prazo)",
        labels={"ano_mes": "Mês de Compra", "pct_no_prazo": "SLA Cumprido (%)"},
    )
    fig.update_traces(line_color=PALETA_AZUL, marker=dict(size=7))
    fig.update_layout(
        yaxis_ticksuffix="%",
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis_title="",
        yaxis_title="SLA (%)",
    )
    return fig


def grafico_faixas_nota(df: pd.DataFrame) -> go.Figure:
    """Gráfico de barras: Nota média e % de notas críticas por faixa de pontualidade."""
    df_sorted = df.sort_values(by="ordem", ascending=True)
    fig = px.bar(
        df_sorted,
        x="faixa_pontualidade",
        y="nota_media",
        text="nota_media",
        title="03 · Impacto do Prazo na Avaliação do Cliente (Nota Média)",
        labels={"faixa_pontualidade": "Pontualidade", "nota_media": "Nota Média (1 a 5)"},
    )
    fig.update_traces(
        marker_color=[PALETA_VERDE if n >= 4.0 else PALETA_DESTAQUE for n in df_sorted["nota_media"]],
        texttemplate="%{text:.2f}",
        textposition="outside",
    )
    fig.update_layout(
        yaxis_range=[1, 5.2],
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis_title="",
        yaxis_title="Nota (1 a 5)",
    )
    return fig


def grafico_gargalo_etapas(df: pd.DataFrame) -> go.Figure:
    """Gráfico de barras horizontais: Dias médios por etapa da cadeia logística."""
    df_sorted = df.sort_values(by="ordem", ascending=False)
    fig = px.bar(
        df_sorted,
        x="dias_medio",
        y="etapa",
        orientation="h",
        text="dias_medio",
        title="05 · Decomposição de Tempo: Despacho vs Trânsito",
        labels={"etapa": "Etapa", "dias_medio": "Dias Médios"},
    )
    fig.update_traces(
        marker_color=PALETA_AZUL,
        texttemplate="%{text:.1f} dias",
        textposition="outside",
    )
    fig.update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis_title="Dias",
        yaxis_title="",
    )
    return fig


def grafico_logistica_uf(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Gráfico de barras horizontais: Top UFs com melhor pontualidade."""
    # Filtra e inverte para o maior ficar no topo visual
    df_top = df.head(top_n).iloc[::-1]
    fig = px.bar(
        df_top,
        x="pct_no_prazo",
        y="uf",
        orientation="h",
        text="pct_no_prazo",
        title=f"04 · Cumprimento de SLA por Estado (Top {top_n} UFs)",
        labels={"uf": "Estado", "pct_no_prazo": "SLA (%)"},
    )
    fig.update_traces(
        marker_color=PALETA_AZUL,
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )
    fig.update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis_title="SLA (%)",
        yaxis_title="",
    )
    return fig


def grafico_sellers_prazo(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Gráfico de barras horizontais: Top vendedores consistentes em prazo."""
    df_top = df.head(top_n).iloc[::-1]
    fig = px.bar(
        df_top,
        x="pct_no_prazo",
        y="vendedor_id",
        orientation="h",
        text="pct_no_prazo",
        title=f"06 · Sellers de Alta Performance em Pontualidade (Top {top_n})",
        labels={"vendedor_id": "Vendedor", "pct_no_prazo": "SLA (%)"},
    )
    fig.update_traces(
        marker_color=PALETA_VERDE,
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )
    fig.update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis_title="SLA (%)",
        yaxis_title="",
    )
    return fig
