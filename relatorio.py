"""Gerador de Relatório HTML Estático e Autônomo.

Executável com: uv run python relatorio.py
Lê os marts via painel.ler(), reutiliza as funções de gráficos do painel.py e
gera relatorio.html sem depender do Streamlit ou de servidor ativo.
"""

from datetime import datetime
from pathlib import Path
import sys
import painel
from pipeline.db import DB_PATH

MARTS_RELATORIO = [
    "kpis_logistica",
    "sla_mensal",
    "faixas_pontualidade_vs_nota",
    "logistica_por_uf",
    "gargalo_etapas",
    "ranking_sellers_logistica",
]

HTML_PATH = Path("relatorio.html")


def gerar_relatorio(db_path: Path | str = DB_PATH, html_path: Path = HTML_PATH) -> None:
    """Gera o arquivo HTML com cartões e gráficos estáticos congelados."""
    dados = painel.ler(MARTS_RELATORIO, db_path=db_path)
    
    # 1. Cartões
    row_kpi = dados["kpis_logistica"].iloc[0]
    sla_pct = painel.pct(row_kpi["pct_no_prazo"])
    espera = painel.dias(row_kpi["dias_medio_entrega"])
    antecipacao = painel.dias(row_kpi["dias_medio_antecipacao"])
    nota = painel.numero(row_kpi["nota_media"], casas=2)
    nota_baixa = painel.pct(row_kpi["pct_nota_baixa"])
    entregas = painel.numero(row_kpi["pedidos_entregues"])

    # 2. Gráficos (div_ids fixos para reprodutibilidade)
    # Período padrão recortado
    df_sla = dados["sla_mensal"]
    fig_sla = painel.grafico_sla_mensal(df_sla)
    html_g01 = fig_sla.to_html(full_html=False, include_plotlyjs="cdn", div_id="g01")
    
    fig_nota = painel.grafico_faixas_nota(dados["faixas_pontualidade_vs_nota"])
    html_g02 = fig_nota.to_html(full_html=False, include_plotlyjs=False, div_id="g02")
    
    fig_etapas = painel.grafico_gargalo_etapas(dados["gargalo_etapas"])
    html_g03 = fig_etapas.to_html(full_html=False, include_plotlyjs=False, div_id="g03")
    
    fig_uf = painel.grafico_logistica_uf(dados["logistica_por_uf"], top_n=10)
    html_g04 = fig_uf.to_html(full_html=False, include_plotlyjs=False, div_id="g04")
    
    fig_sellers = painel.grafico_sellers_prazo(dados["ranking_sellers_logistica"], top_n=10)
    html_g05 = fig_sellers.to_html(full_html=False, include_plotlyjs=False, div_id="g05")

    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")

    # 3. Montagem do HTML completo
    conteudo_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olist · Relatório Operacional de Logística</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f8fafc;
            color: #0f172a;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 24px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 16px;
        }}
        h1 {{
            margin: 0 0 8px 0;
            font-size: 28px;
            color: #1e293b;
        }}
        .subtitulo {{
            color: #64748b;
            font-size: 15px;
            margin: 0;
        }}
        .grid-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .card-rotulo {{
            font-size: 13px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .card-valor {{
            font-size: 26px;
            font-weight: 700;
            color: #0f172a;
        }}
        .secao-grafico {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .grid-duplo {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }}
        @media (max-width: 900px) {{
            .grid-duplo {{ grid-template-columns: 1fr; }}
        }}
        footer {{
            text-align: center;
            color: #94a3b8;
            font-size: 13px;
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #e2e8f0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📦 Olist · Relatório Operacional de Logística</h1>
            <p class="subtitulo">Visão consolidada da operação, SLAs e satisfação do cliente (jan/2017 a ago/2018)</p>
        </header>

        <section class="grid-cards">
            <div class="card">
                <div class="card-rotulo">SLA Cumprido</div>
                <div class="card-valor">{sla_pct}</div>
            </div>
            <div class="card">
                <div class="card-rotulo">Espera Média</div>
                <div class="card-valor">{espera}</div>
            </div>
            <div class="card">
                <div class="card-rotulo">Antecipação Média</div>
                <div class="card-valor">{antecipacao}</div>
            </div>
            <div class="card">
                <div class="card-rotulo">Nota Média</div>
                <div class="card-valor">{nota}</div>
            </div>
            <div class="card">
                <div class="card-rotulo">Notas Críticas</div>
                <div class="card-valor">{nota_baixa}</div>
            </div>
            <div class="card">
                <div class="card-rotulo">Entregas Totais</div>
                <div class="card-valor">{entregas}</div>
            </div>
        </section>

        <section class="secao-grafico">
            {html_g01}
        </section>

        <div class="grid-duplo">
            <section class="secao-grafico">
                {html_g02}
            </section>
            <section class="secao-grafico">
                {html_g03}
            </section>
        </div>

        <div class="grid-duplo">
            <section class="secao-grafico">
                {html_g04}
            </section>
            <section class="secao-grafico">
                {html_g05}
            </section>
        </div>

        <footer>
            Dados gerados em {data_geracao} · Relatório estático autônomo (não requer servidor de dados ativo).
        </footer>
    </div>
</body>
</html>
"""
    html_path.write_text(conteudo_html, encoding="utf-8")
    tamanho_kb = html_path.stat().st_size / 1024
    print(f"✓ Relatório gerado: {html_path.resolve()} ({tamanho_kb:.1f} KB)")


if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    gerar_relatorio()
