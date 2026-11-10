"""Testes unitários do módulo relatorio."""

from pathlib import Path
import re
import pytest
from pipeline.db import get_connection, init_db
import relatorio


def preparar_marts_minimos(db_file: Path) -> None:
    init_db(db_file)
    with get_connection(db_file, read_only=False) as con:
        con.execute(
            """
            CREATE TABLE marts.kpis_logistica AS 
            SELECT 100 AS pedidos_entregues, 90.0 AS pct_no_prazo, 12.0 AS dias_medio_entrega, 
                   5.0 AS dias_medio_antecipacao, 4.2 AS nota_media, 8.0 AS pct_nota_baixa;
            """
        )
        con.execute(
            """
            CREATE TABLE marts.sla_mensal AS 
            SELECT '2017-01' AS ano_mes, 100 AS pedidos_entregues, 90 AS pedidos_no_prazo, 90.0 AS pct_no_prazo, 12.0 AS dias_medio_entrega;
            """
        )
        con.execute(
            """
            CREATE TABLE marts.faixas_pontualidade_vs_nota AS 
            SELECT 1 AS ordem, 'No prazo' AS faixa_pontualidade, 90 AS pedidos_avaliados, 4.5 AS nota_media, 5.0 AS pct_nota_baixa;
            """
        )
        con.execute(
            """
            CREATE TABLE marts.logistica_por_uf AS 
            SELECT 'SP' AS uf, 50 AS entregues, 95.0 AS pct_no_prazo, 8.0 AS dias_medio_real, 15.0 AS dias_medio_previsto, 7.0 AS dias_delta_medio;
            """
        )
        con.execute(
            """
            CREATE TABLE marts.gargalo_etapas AS 
            SELECT 1 AS ordem, 'Despacho' AS etapa, 2.0 AS dias_medio, 2.0 AS dias_mediana;
            """
        )
        con.execute(
            """
            CREATE TABLE marts.ranking_sellers_logistica AS 
            SELECT 'v1' AS vendedor_id, 'SP' AS uf, 25 AS pedidos_entregues, 96.0 AS pct_no_prazo, 7.5 AS dias_medio_entrega;
            """
        )


def test_relatorio_html_gerado_com_sucesso(tmp_path: Path) -> None:
    db_file = tmp_path / "test_relatorio.duckdb"
    preparar_marts_minimos(db_file)
    
    html_out = tmp_path / "relatorio.html"
    
    relatorio.gerar_relatorio(db_path=db_file, html_path=html_out)
    
    assert html_out.exists()
    conteudo = html_out.read_text(encoding="utf-8")
    
    # Verifica se os IDs fixos dos gráficos estão presentes
    assert 'id="g01"' in conteudo
    assert 'id="g02"' in conteudo
    
    # Verifica tamanho menor que 200 KB
    tamanho_kb = html_out.stat().st_size / 1024
    assert tamanho_kb < 200.0


def test_rodar_duas_vezes_muda_apenas_data_do_rodape(tmp_path: Path) -> None:
    db_file = tmp_path / "test_duas_vezes.duckdb"
    preparar_marts_minimos(db_file)
    
    html_out = tmp_path / "relatorio.html"
    
    relatorio.gerar_relatorio(db_path=db_file, html_path=html_out)
    c1 = html_out.read_text(encoding="utf-8")
    
    relatorio.gerar_relatorio(db_path=db_file, html_path=html_out)
    c2 = html_out.read_text(encoding="utf-8")
    
    # Normaliza a data/hora para comparação de conteúdo
    padrao_data = re.compile(r"Dados gerados em \d{2}/\d{2}/\d{4} \d{2}:\d{2}")
    norm1 = padrao_data.sub("DATA_NORMALIZADA", c1)
    norm2 = padrao_data.sub("DATA_NORMALIZADA", c2)
    
    assert norm1 == norm2
