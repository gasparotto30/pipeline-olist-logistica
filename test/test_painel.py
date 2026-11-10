"""Testes unitários do módulo painel."""

from pathlib import Path
import pandas as pd
import painel
from pipeline.db import get_connection, init_db


def test_formatacao_numero_e_moeda() -> None:
    # Testes com dados inventados
    assert painel.numero(1234567, casas=0) == "1.234.567"
    assert painel.numero(1234.56, casas=2) == "1.234,56"
    assert painel.reais(1003862.14) == "R$ 1.003.862,14"
    assert painel.pct(93.2, casas=1) == "93,2%"
    assert painel.dias(12.5) == "12,5 dias"
    assert painel.numero(None) == "-"


def test_figuras_plotly_geram_pontos_compativeis() -> None:
    # DataFrame inventado com 3 linhas
    df_sla = pd.DataFrame([
        {"ano_mes": "2017-01", "pct_no_prazo": 90.0},
        {"ano_mes": "2017-02", "pct_no_prazo": 92.5},
        {"ano_mes": "2017-03", "pct_no_prazo": 88.0},
    ])
    fig = painel.grafico_sla_mensal(df_sla)
    assert len(fig.data[0].x) == 3

    # Faixas nota
    df_faixas = pd.DataFrame([
        {"ordem": 1, "faixa_pontualidade": "No prazo", "nota_media": 4.5},
        {"ordem": 2, "faixa_pontualidade": "Atrasado", "nota_media": 2.1},
    ])
    fig_nota = painel.grafico_faixas_nota(df_faixas)
    assert len(fig_nota.data[0].x) == 2

    # Gargalo etapas
    df_etapas = pd.DataFrame([
        {"ordem": 1, "etapa": "Despacho", "dias_medio": 2.5},
        {"ordem": 2, "etapa": "Transporte", "dias_medio": 10.0},
    ])
    fig_etapas = painel.grafico_gargalo_etapas(df_etapas)
    assert len(fig_etapas.data[0].y) == 2


def test_painel_ler_retorna_dataframes_corretos(tmp_path: Path) -> None:
    db_file = tmp_path / "test_read.duckdb"
    init_db(db_file)
    with get_connection(db_file, read_only=False) as con:
        con.execute("CREATE TABLE marts.kpis_logistica AS SELECT 95.0 AS pct_no_prazo;")
        
    resultado = painel.ler(["kpis_logistica"], db_path=db_file)
    assert "kpis_logistica" in resultado
    assert resultado["kpis_logistica"].iloc[0]["pct_no_prazo"] == 95.0

